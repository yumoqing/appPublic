# `ipgetter` 模块技术文档

> **版本**: `0.6`  
> **作者**: phoemur@gmail.com  
> **许可证**: [WTFPL v2](http://www.wtfpl.net/) — Do What The Fuck You Want To Public License  

---

## 简介

`ipgetter` 是一个轻量级的 Python 模块，用于从互联网获取用户的**外部 IP 地址（公网 IP）**。该模块特别适用于位于 NAT（网络地址转换）后的设备或路由器后端主机。

它通过随机轮询多个公开的 IP 查询服务来减少对单一服务器的请求压力，并具备容错机制以应对部分服务不可用的情况。

所有服务器响应内容使用正则表达式解析提取 IP，支持自定义解析器，兼容 Python 2.5+ 及 Python 3.x。

---

## 安装与依赖

### 安装方式

本模块为单文件脚本，无需安装：

```bash
wget https://raw.githubusercontent.com/phoemur/ipgetter/master/ipgetter.py
```

或直接复制代码保存为 `ipgetter.py`，然后在项目中导入即可。

### 依赖说明

- 标准库：
  - `re`, `json`, `time`, `random`, `socket`, `threading.Timer`
  - `urllib.request`（通过 `future.moves.urllib.request` 兼容 Py2/Py3）
- 第三方兼容层（仅需标准库）：
  - 使用了 `future` 库中的跨版本模块路径（但仍只依赖标准库功能）

> ⚠️ 注意：虽然引入了 `future.moves.urllib.request`，但并未强制要求安装 `future` 包。若环境不支持，请确保运行于原生 Python 2.7+ 或 3.x 环境。

---

## 快速开始

### 基础用法

```python
import ipgetter

# 获取当前公网 IP
myip = ipgetter.myip()
print(myip)  # 输出示例: '8.8.8.8'
```

### 高级测试（调试模式）

```python
ipgetter.IPgetter().test()
```

输出将显示所有服务器返回的结果统计，便于验证一致性与可用性。

---

## API 接口详解

### 函数：`myip() → str`

返回当前机器的公网 IP 地址字符串，失败时返回空字符串。

#### 示例：

```python
>>> import ipgetter
>>> ipgetter.myip()
'203.0.113.45'
```

#### 实现逻辑：

调用 `IPgetter().get_external_ip()` 方法完成实际工作。

---

### 类：`IPgetter`

核心类，提供灵活的 IP 查询控制能力。

#### 构造函数：`__init__()`

初始化一个 `IPgetter` 实例，包含以下属性：

| 属性 | 类型 | 描述 |
|------|------|------|
| `server_list` | list[str] | 支持的 IP 查询服务 URL 列表（共 18 个默认源） |
| `parsers` | dict[str → callable] | 自定义每个服务器响应体的解析函数映射表 |
| `timeout` | float | 单次请求超时时间（单位：秒，默认 `1.6` 秒） |
| `url` | file-like / None | 当前打开的 URL 资源句柄（用于手动关闭） |

> 📌 提示：可通过 `add_server()` 动态添加新的查询服务。

#### 方法：`get_external_ip() → str`

从随机打乱的服务器列表中依次尝试获取公网 IP，直到成功且符合非私有 IP 规则为止。

##### 返回值：

- 成功时返回合法公网 IPv4 字符串（如 `'8.8.8.8'`）
- 失败或未匹配有效 IP 时返回 `''`

##### 过滤规则：

自动排除以下私有/本地地址段：

- `192.*` 开头（典型局域网）
- `10.*` 开头（内网地址）
- `127.*` 开头（回环地址）

> ✅ 此设计避免误取本地接口地址。

##### 执行流程：

1. 打乱 `server_list` 防止单点负载过高
2. 循环调用 `fetch(server)` 获取响应
3. 使用对应解析器提取 IP（默认使用内置正则）
4. 若得到有效公网 IP，则立即返回
5. 否则继续下一个服务，全部失败返回空串

---

#### 方法：`fetch(server: str) → str`

向指定服务发起 HTTP 请求并返回其响应中提取出的 IP 地址。

##### 参数：

- `server`: 目标服务的完整 URL（必须以 `http://` 或 `https://` 开头）

##### 内部处理细节：

- 设置 User-Agent 模拟 Firefox 浏览器请求
- 支持设置超时（兼容 Python 2.5 的 socket hack）
- 使用定时器防止阻塞过久（尤其在旧版 Python 上）
- 自动处理字符编码（优先 UTF-8，失败转 ISO-8859-1）
- 异常捕获并打印错误信息（不影响主流程）

##### 编码处理策略：

```python
if PY3K:
    try:
        content = content.decode('UTF-8')
    except UnicodeDecodeError:
        content = content.decode('ISO-8859-1')
```

> ❗ 不依赖第三方库（如 `chardet`），坚持使用标准库。

##### 资源清理：

无论成功与否，均确保关闭连接、取消定时器、恢复原始 socket 超时设置。

---

#### 方法：`defaultparser(content: str) → str`

默认的 IP 解析函数，使用正则表达式从文本中提取第一个匹配的 IPv4 地址。

##### 正则表达式：

```regex
(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.
(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.
(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.
(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)
```

✅ 支持完整的 IPv4 地址格式校验。

##### 行为：

- 成功提取则返回 IP 字符串
- 匹配失败或异常抛出则返回 `''`

---

#### 方法：`add_server(server: str, parser: callable)`

动态注册一个新的 IP 查询服务及其专属解析函数。

##### 参数：

- `server`: 新增服务的 URL（例如 `'https://api.ipify.org?format=json'`）
- `parser`: 接受 `content: str` 输入并返回 `ip: str` 的可调用对象

##### 示例：

```python
def parse_ipinfo_json(content):
    data = json.loads(content)
    return data['ip']

g = IPgetter()
g.add_server('http://ipinfo.io/json', parse_ipinfo_json)
print(g.get_external_ip())
```

> 💡 常用于 JSON 接口的服务扩展。

---

#### 方法：`test()`

测试所有服务器的一致性和可达性，输出汇总报告。

##### 输出内容：

- 总服务器数量
- 各 IP 地址出现次数统计
- 每个服务的实际响应结果字典

##### 示例输出：

```
Number of servers: 18
IP's :
8.8.8.8 = 16 occurrences
broken server = 2 occurrences

{'http://ifconfig.me/ip': '8.8.8.8', ...}
```

> 🔍 适合开发者调试或评估服务稳定性。

---

#### 方法：`all_result()`

遍历所有服务器并打印 `[url, response]` 对列表（调试用途）。

⚠️ 当前实现仅为简单打印，无返回值。

---

## 内置服务器列表（截至 v0.6）

以下是模块默认使用的公共 IP 查询服务（共 18 个）：

```text
- http://ifconfig.me/ip
- http://ipecho.net/plain
- http://getmyipaddress.org/
- http://www.my-ip-address.net/
- http://www.canyouseeme.org/
- http://trackip.net/
- http://icanhazip.com/
- http://www.ipchicken.com/
- http://whatsmyip.net/
- http://www.lawrencegoetz.com/programs/ipinfo/
- http://ip-lookup.net/
- http://ipgoat.com/
- http://www.myipnumber.com/my-ip-address.asp
- http://www.geoiptool.com/
- http://checkip.dyndns.com/
- http://www.ip-adress.eu/
- http://wtfismyip.com/
- http://httpbin.org/ip
```

> 🔄 所有服务按随机顺序访问，降低单点压力。

> 🛠 如需增删服务，请联系作者 via GitHub。

---

## 使用建议与注意事项

### ✅ 最佳实践

- 在生产环境中定期调用 `.myip()` 获取最新 IP。
- 若发现某些服务频繁失效，可通过 `add_server()` 替换更稳定的替代源。
- 使用 `.test()` 定期检查服务健康状态。

### ⚠️ 注意事项

- 仅支持 IPv4（目前无 IPv6 支持）
- 不保证 100% 准确率（取决于第三方服务可用性）
- 错误请求可能触发某些服务的限流机制
- 超时设置较短（1.6s），适合快速探测，高延迟网络下可适当调大

---

## 许可证

```
Copyright 2014 phoemur@gmail.com

This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.
```

👉 即：你可以自由地使用、修改、分发此代码，只要你不违法。

---

## 贡献与反馈

欢迎提交 Issue 或 Pull Request 至 GitHub 仓库：

🔗 [https://github.com/phoemur/ipgetter](https://github.com/phoemur/ipgetter)

若您希望添加或移除某个 IP 查询服务，请联系作者。

---

## 示例：扩展 JSON 接口支持

```python
import ipgetter
import json

def parse_ipinfo(content):
    return json.loads(content)['ip']

g = ipgetter.IPgetter()
g.add_server('http://ipinfo.io/json', parse_ipinfo)
print("My public IP is:", g.get_external_ip())
```

---

## 版本历史

| 版本 | 说明 |
|------|------|
| `0.6` | 当前版本，优化健壮性，增加可扩展性 |
| `0.5` | 初始开源版本 |

---

## 致谢

感谢以下服务提供免费的 IP 查询接口：

- ifconfig.me
- icanhazip.com
- ipinfo.io
- httpbin.org
- dyndns 等

🙏 维护这些开放资源的人们让此类工具成为可能。

--- 

📘 文档最后更新：2025年4月5日