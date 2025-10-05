# 技术文档：Python 日志记录模块

```markdown
# MyLogger 模块技术文档

## 概述

本模块提供一个轻量级、线程安全（基于单例模式）的日志记录工具，支持多级别日志输出，并可将日志写入文件或标准输出。该模块通过 `inspect` 模块自动获取调用上下文信息（如文件名、行号），并结合时间戳生成结构化日志。

---

## 依赖项

- `sys`: 用于访问标准输出流。
- `codecs`: 提供带编码支持的文件读写功能（UTF-8）。
- `traceback.format_exc`: 用于捕获和格式化异常堆栈信息。
- `appPublic.timeUtils.timestampstr`: 返回当前时间的时间戳字符串（格式依赖具体实现）。
- `appPublic.Singleton.SingletonDecorator`: 单例装饰器，确保 `MyLogger` 类为单例模式。
- `inspect`: 获取运行时调用栈信息，用于提取调用者文件名和行号。

> ⚠️ 注意：`appPublic.*` 是自定义公共库，请确保其已正确安装并可导入。

---

## 核心类：`MyLogger`

### 装饰器
```python
@SingletonDecorator
class MyLogger:
```
使用 `SingletonDecorator` 确保每个 `name` 对应唯一的 `MyLogger` 实例（注意：当前实现中未按 name 区分实例，可能存在设计缺陷 —— 见【注意事项】）。

---

### 属性说明

| 属性 | 类型 | 描述 |
|------|------|------|
| `levels` | `dict` | 定义日志级别及其优先级数值（数字越大，优先级越高）。 |
| `formater` | `str` | 日志输出格式模板，兼容 `%` 格式化语法。 |

#### 日志级别说明（按优先级从高到低）

| 级别名称 | 数值 | 用途 |
|---------|-----|------|
| `clientinfo` | 7 | 客户端相关信息，最高优先级 |
| `info`       | 6 | 常规信息提示 |
| `debug`      | 5 | 调试信息 |
| `warning`    | 4 | 警告信息 |
| `error`      | 3 | 错误信息 |
| `exception`  | 2 | 异常堆栈信息 |
| `critical`   | 1 | 致命错误，最低优先级 |

> 输出规则：仅当日志条目的级别 ≤ 当前 logger 的 `level` 时才会被记录。

---

### 构造函数：`__init__(self, name, levelname='debug', logfile=None)`

#### 参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `name` | `str` | 必填 | 日志记录器名称，用于标识来源 |
| `levelname` | `str` | `'debug'` | 初始日志级别，决定哪些消息会被输出 |
| `logfile` | `str or None` | `None` | 日志文件路径；若为 `None`，则输出到 `sys.stdout` |

#### 初始化行为

- 设置 `self.name`, `self.levelname`, `self.level`（对应数值）
- 设置 `self.logfile` 和初始 `self.logger = None`

---

### 方法说明

#### `open_logger(self)`
打开日志目标：
- 若指定了 `logfile`，以追加模式 (`a`) 打开文件，使用 UTF-8 编码。
- 否则，使用 `sys.stdout` 作为输出流。

> 使用 `codecs.open` 确保 Unicode 写入安全。

#### `close_logger(self)`
关闭已打开的日志文件句柄（如果存在），并将 `self.logger` 设为 `None`。

> ❗ 存在 bug：最后一行重复赋值 `self.logger = None` 多余且无意义。

#### `log(self, levelname, message, frame_info)`
核心日志写入方法。

##### 参数
| 参数 | 类型 | 描述 |
|------|------|------|
| `levelname` | `str` | 要记录的日志级别 |
| `message` | `str` | 日志内容 |
| `frame_info` | `frame object` | 调用栈帧对象，来自 `inspect.currentframe()` |

##### 行为流程
1. 获取调用者的栈帧 → 提取 `filename` 和 `lineno`
2. 查询 `levelname` 对应的等级值
3. 如果该等级高于当前 logger 允许的最高等级（即 `level > self.level`），则跳过输出
4. 构造日志数据字典 `data`
5. 调用 `open_logger()` 打开输出
6. 使用 `formater % data` 格式化日志字符串
7. 写入并刷新缓冲区
8. 调用 `close_logger()` 关闭资源

> ✅ 特点：每次写日志都临时打开/关闭文件，适合低频日志场景，避免长期占用句柄。

---

## 辅助函数（全局接口）

提供简洁的日志调用方式，封装了 `MyLogger` 的创建与调用过程。

| 函数 | 等效操作 | 示例 |
|------|----------|-------|
| `clientinfo(message)` | `logger.log('clientinfo', message, ...)` | `clientinfo("用户登录")` |
| `info(message)`        | `logger.log('info', message, ...)`       | `info("任务开始执行")` |
| `debug(message)`       | `logger.log('debug', message, ...)`      | `debug("变量x值为: " + str(x))` |
| `warning(message)`     | `logger.log('warning', message, ...)`    | `warning("配置项缺失")` |
| `error(message)`       | `logger.log('error', message, ...)`      | `error("数据库连接失败")` |
| `critical(message)`    | `logger.log('critical', message, ...)`   | `critical("系统即将退出")` |
| `exception(message)`   | 记录异常堆栈 + 自定义消息               | `exception("处理请求出错")` |

> 📌 `exception()` 特殊处理：自动附加 `traceback.format_exc()` 的完整堆栈跟踪。

---

## 使用示例

```python
from mylogger import info, debug, error, exception

def main():
    info("程序启动")
    debug("正在加载配置...")
    try:
        1 / 0
    except Exception:
        exception("发生数学错误")

if __name__ == '__main__':
    main()
```

输出示例（假设输出到控制台）：
```
2025-04-05 10:20:30.123[Test][info][main.py:5]程序启动
2025-04-05 10:20:30.124[Test][debug][main.py:6]正在加载配置...
2025-04-05 10:20:30.125[exception][exception][main.py:8]发生数学错误
Traceback (most recent call last):
  File "main.py", line 7, in main
    1 / 0
ZeroDivisionError: division by zero
```

---

## 配置说明

### 日志格式化字符串
```python
'%(timestamp)s[%(name)s][%(levelname)s][%(filename)s:%(lineno)s]%(message)s\n'
```

字段解释：

| 字段 | 含义 |
|------|------|
| `%(timestamp)s` | 时间戳（由 `timestampstr()` 提供） |
| `%(name)s`       | Logger 名称 |
| `%(levelname)s` | 日志级别名称 |
| `%(filename)s`   | 发生日志的源文件名 |
| `%(lineno)s`     | 源代码行号 |
| `%(message)s`    | 用户提供的日志消息 |

---

## 注意事项与改进建议

### ⚠️ 已知问题

1. **单例逻辑可能失效**
   - `SingletonDecorator` 可能对所有 `MyLogger` 创建返回同一实例，无法区分不同 `name`。
   - 建议改为基于 `name` 的单例缓存机制。

2. **`close_logger()` 中冗余赋值**
   ```python
   self.logger.close()
   self.logger = None
   self.logger = None  # 重复
   ```
   第二个赋值无效，应删除。

3. **性能考量**
   - 每次 `log()` 都打开/关闭文件，在高频日志场景下效率低下。
   - 建议引入持久化文件句柄管理（如首次打开后保持打开状态）。

4. **缺乏线程安全性**
   - 尽管是“单例”，但未加锁，多线程同时写日志可能导致混乱。
   - 如需多线程支持，建议添加 `threading.Lock`。

5. **硬编码 logger 名称**
   - 所有辅助函数中 `logger = MyLogger('Test')` 固定为 `'Test'`，不合理。
   - 应允许传参或动态设置默认名称。

---

## 总结

本模块实现了基本的日志功能，具备以下优点：

✅ 结构清晰  
✅ 支持自动定位调用位置  
✅ 支持文件/控制台双输出  
✅ 提供丰富的日志级别  
✅ 易于使用的全局函数接口  

适用于小型项目或嵌入式脚本环境。对于大型应用，建议升级至标准库 `logging` 模块或增强此模块的功能与健壮性。
```