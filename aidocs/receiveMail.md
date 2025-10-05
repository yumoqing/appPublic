# 邮件接收与解析工具技术文档

本项目是一个基于 Python 的 POP3 协议邮件接收与解析工具，能够从指定邮箱拉取近期邮件，并对邮件内容进行解码和处理。支持按时间范围过滤邮件，并提供可扩展的回调机制用于自定义处理逻辑。

---

## 📦 依赖库

```python
import poplib
import pdb
import email
from email import header
import re
import time
import datetime
import os
```

### 主要用途：
- `poplib`: 实现 POP3 协议连接，用于收信。
- `email`: 解析 MIME 格式的邮件内容。
- `re`: 正则表达式，用于提取日期信息。
- `time`, `datetime`: 时间处理与格式转换。
- `os`: 文件路径等操作系统操作（未直接使用，保留备用）。

---

## ⚙️ 全局配置变量

| 变量名     | 类型   | 描述 |
|----------|--------|------|
| `POP_ADDR` | str    | POP3 服务器地址，如 `'pop.126.com'` |
| `USER`     | str    | 用户登录邮箱账号（需手动填写） |
| `PASS`     | str    | 用户邮箱密码或授权码（需手动填写） |
| `CONFIG`   | str    | 存储“最近读取时间”的配置文件路径（需手动设置） |

> 🔐 注意：`USER`、`PASS` 和 `CONFIG` 需在使用前由用户显式赋值。

---

## 🕰️ 时间处理函数

### `getYear(date: str) -> int`
从日期字符串中提取年份（匹配 `2xxx` 四位数）。

#### 示例：
```python
getYear("Mon, 15 Apr 2025 10:30:00 +0800")  # 返回 2025
```

---

### `getMonth(date: str) -> int`
根据英文缩写月份（Jan-Dec）返回对应的数字（1-12）。

#### 支持的缩写：
`Jan`, `Feb`, `Mar`, `Apr`, `May`, `Jun`,  
`Jul`, `Aug`, `Sep`, `Oct`, `Nov`, `Dec`

#### 示例：
```python
getMonth("Mon, 15 Apr 2025 10:30:00 +0800")  # 返回 4
```

---

### `getDay(date: str) -> int`
提取日期中的日部分（1-31）。

#### 示例：
```python
getDay("Mon, 15 Apr 2025 10:30:00 +0800")  # 返回 15
```

---

### `getTime(date: str) -> list[int]`
提取时间部分并返回 `[小时, 分钟, 秒]` 整数列表。

#### 示例：
```python
getTime("Mon, 15 Apr 2025 10:30:45 +0800")  # 返回 [10, 30, 45]
```

---

### `transformDate(date: str) -> int`
将标准邮件日期格式转换为一个整数时间戳，便于比较。

#### 输出格式：
`YYYYMMDDHHMMSS`（例如：`20250415103045`）

#### 原理：
依次拼接年、月、日、时、分、秒为一个大整数，支持数值大小比较。

#### 示例：
```python
transformDate("Mon, 15 Apr 2025 10:30:45 +0800")  # 返回 20250415103045
```

---

### `getTimeEarly(period: str) -> str`
计算当前时间往前推一段时间后的时间点（返回 `ctime()` 格式字符串）。

#### 支持的时间单位：
| 单位 | 含义       |
|------|------------|
| `y`  | 年         |
| `m`  | 月         |
| `d`  | 天         |
| `H`  | 小时       |
| `M`  | 分钟       |
| `S`  | 秒         |

#### 示例：
```python
getTimeEarly("1d3H")  # 当前时间减去 1 天 3 小时
```

> ⚠️ 警告：`years` 和 `months` 使用的是 `timedelta`，不精确（Python 原生限制），建议仅用于粗略估算。

---

## 💾 持久化记录功能

### `getRecentReadMailTime() -> str`
读取上次处理邮件的时间（存储于 `CONFIG` 文件中）。

#### 返回：
文件内容原始字符串（通常是 `time.ctime()` 格式）。

---

### `setRecentReadMailTime() -> None`
将当前时间写入 `CONFIG` 文件，标记为“最近已读时间”。

#### 示例文件内容：
```
Mon Apr 15 10:30:45 2025
```

---

## ✉️ 邮件内容解析

### `parseMailContent(msg: Message) -> None`
递归解析邮件正文内容，自动识别编码并输出文本。

#### 特性：
- 支持多部分 MIME 邮件（如 HTML/纯文本混合）
- 自动检测 `charset` 编码
- 若解码失败，默认输出 `"Decode Failed"`

#### 输出方式：
直接打印到控制台（可通过修改实现日志或其他输出）

---

## 📥 核心功能：接收邮件

### `recvEmail(POP_ADDR, USER, PASS, PERIOD, callback) -> None`

#### 参数说明：

| 参数        | 类型     | 说明 |
|-------------|----------|------|
| `POP_ADDR`  | str      | POP3 服务器地址 |
| `USER`      | str      | 登录用户名（邮箱） |
| `PASS`      | str      | 登录密码或授权码 |
| `PERIOD`    | str      | 时间范围，如 `"7d"` 表示最近7天 |
| `callback`  | function | 回调函数，处理每封符合条件的邮件 |

#### 工作流程：
1. 连接到 POP3 服务器并登录。
2. 获取邮件总数及大小。
3. 计算起始时间 `FROMTIME = now - PERIOD`。
4. 按倒序遍历所有邮件（最新优先）。
5. 对每封邮件：
   - 下载原始数据
   - 解析为 `email.message.Message` 对象
   - 提取 `Date` 头部并转换为整数时间
   - 如果邮件时间 **晚于** 起始时间，则调用 `callback(mail)`
   - 若 `callback` 返回 `False`，中断后续处理
6. 遇到第一封过期邮件即停止（因邮件按时间排序）

#### 示例调用：
```python
def my_handler(mail):
    print("发件人:", mail.get('From'))
    print("主题:", header.decode_header(mail.get('Subject'))[0][0])
    parseMailContent(mail)
    return True  # 继续处理下一封

recvEmail(POP_ADDR, USER, PASS, "7d", my_handler)
```

---

## 🧪 调试支持

内置 `pdb.set_trace()` 注释行可用于断点调试：

```python
# pdb.set_trace()
```

取消注释可在关键位置暂停程序执行，方便排查问题。

---

## 🛠️ 使用示例

```python
# 设置参数
USER = 'your_email@126.com'
PASS = 'your_password_or_token'
CONFIG = './last_read_time.txt'

# 定义回调函数
def handle_mail(mail):
    subject = mail.get('Subject')
    sender = mail.get('From')
    date = mail.get('Date')
    print(f"收到来信：{subject} 来自 {sender} 发送于 {date}")
    parseMailContent(mail)
    return True  # 继续处理

# 接收过去 3 天内的邮件
recvEmail(POP_ADDR, USER, PASS, "3d", handle_mail)

# 更新最后读取时间
setRecentReadMailTime()
```

---

## ❗ 注意事项

1. **安全性**：避免将密码硬编码在代码中，建议通过环境变量或配置文件加载。
2. **编码兼容性**：某些非标准编码可能导致解码失败，建议增强异常处理。
3. **性能**：对于大量邮件，应考虑分页或只获取头部优化。
4. **错误处理**：目前缺少网络异常、认证失败等错误捕获，生产环境需补充 `try-except`。
5. **POP3 局限性**：无法像 IMAP 一样标记状态或选择文件夹，仅适合简单场景。

---

## 📌 待改进方向

| 功能 | 建议 |
|------|------|
| 错误处理 | 添加 `try...except` 处理连接超时、认证失败等问题 |
| 日志系统 | 替换 `print()` 为 `logging` 模块 |
| 配置管理 | 使用 JSON/YAML 配置文件替代全局变量 |
| 编码容错 | 增加常见编码尝试（如 gb2312, gbk） |
| 回调规范 | 定义统一的回调接口结构 |

---

## 📎 总结

该脚本适用于轻量级定时任务，例如：
- 监控报警邮件
- 自动采集特定来源邮件内容
- 简单的邮件通知处理器

结合 cron 或 Windows 任务计划，可构建自动化邮件响应系统。

--- 

📄 文档版本：v1.0  
📅 最后更新：2025-04-05