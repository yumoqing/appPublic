# `StreamHttpClient` 技术文档

```markdown
# StreamHttpClient - 异步流式 HTTP 客户端

一个基于 `aiohttp` 和 `aiohttp_socks` 的异步、支持 SOCKS5 代理的流式 HTTP 客户端，具备自动降级到代理机制、SSL 配置管理、连接失败重试等功能。

---

## 📌 概述

`StreamHttpClient` 是一个用于发起异步 HTTP 请求的 Python 类，主要特性包括：

- 支持 **直接请求** 与 **SOCKS5 代理请求**
- 自动检测连接失败并尝试切换至 SOCKS5 代理（智能回退）
- 支持流式响应处理（chunked streaming），适用于大文件或长响应场景
- 可配置 SSL 验证行为（如跳过证书验证）
- 支持上传文件和表单数据
- 维护需要使用代理的 URL 列表（持久化到本地文件）

---

## 🔧 环境依赖

### Python 版本
```bash
Python >= 3.7
```

> 示例中使用的是虚拟环境下的 Python 3.12 路径：
> ```python
> #!/Users/ymq/p3.12/bin/python
> ```

### 第三方库依赖

| 包 | 用途 |
|----|------|
| `aiohttp` | 异步 HTTP 客户端/服务器框架 |
| `aiohttp_socks` | 提供对 SOCKS4/SOCKS5 代理的支持 |
| `certifi` | 提供 Mozilla 的 CA 证书包，用于 SSL 验证 |
| `ssl` | Python 内置模块，用于 SSL/TLS 配置 |

### 可选日志模块
```python
from appPublic.log import exception, debug
```
> 需确保项目中存在此模块，否则需替换为标准日志工具（如 `logging`）。

---

## 📦 核心功能

### ✅ 流式行解析器：`async def liner(async_gen)`
将字节流按 `\n` 分割为每一行，并以异步生成器方式逐行输出。

#### 参数
- `async_gen`: 异步生成器，产出 `bytes` 类型的数据块

#### 返回
- `AsyncGenerator[bytes]`: 每次 `yield` 一行内容（末尾不含 `\n`）

#### 示例用法
```python
async for line in liner(response.content.iter_chunked(1024)):
    print(line.decode('utf-8'))
```

> 注意：原始代码中该函数未被调用，但可作为工具扩展使用。

---

### 🔐 SSL 上下文构建：`get_non_verify_ssl()`
创建一个不验证主机名和证书的 SSL 上下文，用于绕过 HTTPS 证书检查。

#### 返回
- `ssl.SSLContext`: 配置为 `CERT_NONE` 且关闭 `check_hostname` 的上下文

> ⚠️ 安全警告：仅建议在测试或可信网络中使用，生产环境慎用！

---

## 🧱 主要类：`StreamHttpClient`

### 初始化：`__init__(socks5_url="socks5://127.0.0.1:1086")`

#### 参数
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `socks5_url` | str | `"socks5://127.0.0.1:1086"` | 默认使用的 SOCKS5 代理地址 |

#### 动作
- 加载本地保存的需走代理的 URL 列表（从 `~/.socksurls.txt`）
- 创建默认 SSL 上下文（使用 `certifi` 来源的 CA 证书）

#### 属性
| 属性 | 类型 | 描述 |
|------|------|------|
| `socks_urls_file` | Path | 存储代理 URL 列表的文件路径 |
| `socks_urls` | set[str] | 当前已知需要通过 SOCKS 访问的 URL 集合 |
| `ssl_context` | ssl.SSLContext | 默认的安全 SSL 上下文 |

---

### 🔁 私有方法

#### `_load_socks_urls() -> List[str]`
从 `~/.socksurls.txt` 文件读取所有需要走代理的 URL。

> 若文件不存在，则返回空列表。

#### `_save_socks_url(url: str)`
将指定 URL 添加到 `socks_urls` 集合并追加写入 `.socksurls.txt` 文件，防止重复添加。

---

## 🌐 核心请求方法

### `__call__()` 方法（主入口）

异步发起 HTTP 请求，支持自动故障转移至 SOCKS5 代理。

#### 签名
```python
async def __call__(
    self,
    method: str,
    url: str,
    *,
    headers=None,
    params=None,
    data=None,
    json=None,
    files=None,
    chunk_size=1024,
    **kw
)
```

#### 参数说明
| 参数 | 类型 | 描述 |
|------|------|------|
| `method` | str | HTTP 方法（GET, POST 等） |
| `url` | str | 请求目标 URL |
| `headers` | dict | 请求头 |
| `params` | dict | 查询参数（URL query string） |
| `data` | Any | 表单或原始请求体数据 |
| `json` | dict | JSON 序列化数据（会设置 `Content-Type: application/json`） |
| `files` | dict | 文件上传字段，格式：`{"name": (filename, fileobj, content_type)}` |
| `chunk_size` | int | 每次读取响应内容的大小（字节） |
| `verify` | bool | 是否启用 SSL 验证（自定义关键字，非 aiohttp 原生参数） |
| `**kw` | 其他参数 | 传递给 `session.request()` 的其他参数 |

#### 工作流程
1. 判断当前 URL 是否在 `self.socks_urls` 中：
   - 是 → 直接使用 SOCKS5 代理发送请求
   - 否 → 尝试直连
2. 直连失败（`ClientConnectionError`）时：
   - 打印错误日志
   - 切换为 SOCKS5 代理重试
   - 成功后将该 URL 记录进 `~/.socksurls.txt`
3. 其他异常则抛出

#### 日志说明
| 日志符号 | 含义 |
|---------|------|
| `🌐` | 尝试直连 |
| `🔁` | 使用 SOCKS5 代理 |
| `❌` | 请求失败 |
| `🧦` | 正在使用袜子（SOCKS）代理重试 |

---

### `request()` 方法（便捷封装）

同步等待完整响应体返回。

```python
async def request(...)
```

#### 行为
- 调用 `__call__()` 获取所有 chunk
- 合并为完整的 `bytes` 返回

> ⚠️ 对于大型响应，请优先使用 `__call__()` 进行流式处理以避免内存溢出。

---

### `_request_with_connector()` 内部实现

真正执行请求的核心方法。

#### 参数
同 `__call__`，额外包含：
- `use_socks`: 是否使用 SOCKS5 代理
- `ssl_context`: 使用的 SSL 上下文对象

#### 实现细节
- 使用 `ProxyConnector.from_url()` 构造代理连接器（若 `use_socks=True`）
- 支持动态选择 SSL 验证模式：
  - 若 `verify=False` 在 kw 中 → 使用无验证 SSL 上下文
  - 否则使用默认安全上下文
- 处理 `files` 和 `data/json` 的编码逻辑：
  - 存在 `files` → 构造 `FormData`
  - 否则根据是否有 `json` 参数决定使用 `json=` 或 `data=`
- 使用 `session.request()` 发起请求
- 流式读取响应内容（`iter_chunked(chunk_size)`）

---

## 💡 使用示例

### 基本 GET 请求
```python
hc = StreamHttpClient()
response = await hc.request("GET", "https://httpbin.org/get")
print(response.decode())
```

### POST JSON 数据
```python
payload = {"key": "value"}
resp = await hc.request("POST", "https://httpbin.org/post", json=payload)
print(resp.decode())
```

### 文件上传
```python
with open("test.txt", "rb") as f:
    files = {
        "file": ("test.txt", f, "text/plain")
    }
    data = {"meta": "info"}
    resp = await hc.request("POST", "https://example.com/upload", data=data, files=files)
```

### 忽略 SSL 验证（谨慎使用）
```python
resp = await hc.request("GET", "https://self-signed.badssl.com/", verify=False, timeout=5)
```

---

## 🖥️ CLI 主程序（测试入口）

当脚本直接运行时，执行简单测试请求。

### 用法
```bash
python stream_http_client.py "your prompt"
```

> 当前示例中未实际使用 `prompt`，而是固定请求百度首页。

#### 示例输出
```bash
b'<!DOCTYPE html>...'
```

---

## 📁 文件结构影响

### 创建的本地文件
- `~/.socksurls.txt`
  - 存储曾经因直连失败而改用 SOCKS5 的 URL 列表
  - 每行一个 URL，自动去重

> 示例：
```
https://blocked-site.com
https://internal-api.example.org
```

---

## ⚠️ 注意事项 & 最佳实践

1. **安全性**
   - `verify=False` 会禁用 SSL 验证，可能导致中间人攻击。
   - 生产环境中应尽量避免使用。

2. **性能**
   - 流式接口适合处理大响应；小请求推荐使用 `request()` 获取完整结果。
   - `chunk_size` 可调节性能与延迟平衡。

3. **异常处理**
   - 所有非连接类异常都会重新抛出。
   - 建议外部捕获 `Exception` 并做适当处理。

4. **日志系统依赖**
   - 依赖 `appPublic.log.debug` 和 `.exception` 函数。
   - 如不可用，请替换为标准 `logging` 模块。

---

## 🛠 TODO / 改进建议

| 功能 | 建议 |
|------|------|
| 更灵活的日志注入 | 支持传入 logger 实例 |
| 支持更多代理类型 | 如 HTTP 代理、认证代理等 |
| 自动清理无效 URL | 定期验证 `.socksurls.txt` 中的链接是否仍需代理 |
| 支持超时配置 | 允许用户自定义 `timeout` 对象而非仅秒数 |
| 增加单元测试 | 覆盖直连、代理、失败回退等场景 |

---

## 📎 License

MIT（假设）  
作者：未知  
更新时间：2025年4月

> 请结合实际项目规范进行调整。
```