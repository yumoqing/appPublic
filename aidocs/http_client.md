# HTTP 客户端库技术文档

这是一个基于 `requests` 库封装的 Python HTTP 客户端工具类，提供了自动会话管理、异常处理和简化接口调用的功能。适用于需要与 Web API 交互的应用场景。

---

## 目录

- [概述](#概述)
- [依赖](#依赖)
- [异常类型](#异常类型)
- [全局变量](#全局变量)
- [Http_Client 类](#http_client-类)
  - [`__init__`](#__init__)
  - [`prepped_handler`](#prepped_handler)
  - [`response_handler`](#response_handler)
  - [`url2domain`](#url2domain)
  - [`_webcall`](#_webcall)
  - [`webcall`](#webcall)
  - [`__call__`](#__call__)
  - [HTTP 方法封装](#http-方法封装)
    - `get`
    - `post`
    - `put`
    - `delete`
    - `option`
- [使用示例](#使用示例)

---

## 概述

`Http_Client` 是一个轻量级的 HTTP 客户端封装类，主要功能包括：

- 自动维护每个域名的 `session`（通过 Cookie 中的 `Set-Cookie` 提取并设置）
- 支持常见的 HTTP 方法（GET、POST、PUT、DELETE、OPTION）
- 统一处理响应状态码，并抛出相应异常
- 对 JSON 响应进行解析，提取业务数据（如 `data` 字段）

---

## 依赖

- `requests`：用于底层 HTTP 请求处理  
  安装方式：
  ```bash
  pip install requests
  ```

> ⚠️ 注意：该客户端默认禁用了 SSL 验证（`verify=False`），在生产环境中应谨慎使用。

---

## 异常类型

### `NeedLogin`
当服务器返回 `401 Unauthorized` 时抛出，表示当前请求未登录或认证失败。

```python
raise NeedLogin
```

### `InsufficientPrivilege`
当服务器返回 `403 Forbidden` 时抛出，表示权限不足。

```python
raise InsufficientPrivilege
```

### `HTTPError`
当服务器返回非 `200` 状态码时抛出，包含状态码和请求 URL。

#### 属性
| 属性名       | 类型   | 说明             |
|-------------|--------|------------------|
| `resp_code` | int    | HTTP 响应状态码   |
| `url`       | str    | 请求的完整 URL     |

#### 方法
- `__str__()` 和 `__expr__()`：返回格式为 `{url}:{resp_code}` 的字符串

> ❗注意：`__expr__` 可能是拼写错误，通常应为 `__repr__`。建议修复此方法名为 `__repr__`。

---

## 全局变量

### `hostsessions: dict`
存储每个域名对应的 session ID（从 `Set-Cookie` 头部提取），键为协议+主机名（例如 `https://api.example.com`），值为 session 字符串。

用途：实现跨请求的会话保持。

---

## Http_Client 类

### `__init__()`
初始化一个 `Http_Client` 实例。

#### 行为
- 创建一个持久化的 `requests.Session()` 实例
- 关闭 SSL 证书验证（`verify=False`）
- 注册响应钩子 `response_handler`

> 🔒 安全提示：关闭 SSL 验证可能导致中间人攻击，仅建议在测试环境使用。

---

### `prepped_handler(prepped)`
预请求处理器，可用于修改准备好的请求对象（如添加签名、日志等）。

#### 参数
- `prepped` (`PreparedRequest`)：已准备好的请求对象

#### 默认行为
无操作（`pass`），可由子类重写以扩展功能。

---

### `response_handler(resp, *args, **kw)`
响应处理器钩子函数，在每次收到响应后触发。

#### 参数
- `resp` (`Response`)：响应对象
- `*args`, `**kw`：额外参数（保留扩展性）

#### 返回值
- 返回原始 `resp`，不影响后续处理

> ✅ 可用于记录日志、性能监控等。

---

### `url2domain(url)`
从完整 URL 提取协议 + 主机部分（即域名层级）

#### 参数
- `url` (`str`)：完整的 URL 地址

#### 返回值
- `str`：形如 `https://example.com` 的字符串

#### 示例
```python
client.url2domain("https://api.example.com/v1/users?id=1")
# 结果: "https://api.example.com"
```

#### 实现逻辑
取前三个 `/` 分隔的部分（协议、空、主机）

---

### `_webcall(...)`
核心 HTTP 请求执行方法，负责发送请求并处理基础响应。

#### 参数
| 参数      | 类型     | 默认值 | 说明 |
|----------|---------|-------|------|
| `url`     | str     | 必填   | 请求地址 |
| `method`  | str     | `"GET"` | HTTP 方法（GET/POST/PUT/DELETE/OPTION） |
| `params`  | dict    | `{}`  | GET 请求为查询参数；非 GET 为表单数据 |
| `files`   | dict    | `{}`  | 文件上传字段 |
| `headers` | dict    | `{}`  | 自定义请求头 |
| `stream`  | bool    | `False` | 是否启用流式响应 |

#### 内部流程
1. 解析域名 → 获取对应 session ID
2. 若存在 session，则在 headers 中加入 `'session': sessionid`
3. 构造 `Request` 对象并准备为 `PreparedRequest`
4. 调用 `prepped_handler()` 进行预处理
5. 发送请求
6. 处理响应：
   - 状态码 `200`：检查是否有 `Set-Cookie`，更新 `hostsessions`
   - `401`：抛出 `NeedLogin`
   - `403`：抛出 `InsufficientPrivilege`
   - 其他非 `200`：打印错误信息并抛出 `HTTPError`

#### 返回值
- 成功时返回 `requests.Response` 对象

---

### `webcall(...)`
对 `_webcall` 的增强包装，主要用于处理响应体内容。

#### 参数
同 `_webcall`

#### 功能
- 调用 `_webcall` 执行请求
- 若 `stream=True`，直接返回响应对象
- 否则尝试将响应解析为 JSON：
  - 若解析成功且结果为字典：
    - 检查是否存在 `'status'` 字段
    - 若 `status == 'OK'`，返回 `'data'` 字段内容
    - 否则返回整个 JSON 数据
  - 若不是字典或无 `status`，原样返回
- 若 JSON 解析失败，返回文本内容（`resp.text`）

#### 返回值
- 解析后的数据（dict / list / str）或原始响应文本

---

### `__call__(...)`
使实例可被直接调用，代理到 `webcall` 方法。

#### 示例
```python
client = Http_Client()
result = client("https://api.example.com/data", method="GET")
```

---

## HTTP 方法封装

提供常用 HTTP 方法的快捷调用方式。

| 方法 | 等效于 |
|------|--------|
| `.get(...)`     | `client(url, method='GET', ...)` |
| `.post(...)`    | `client(url, method='POST', ...)` |
| `.put(...)`     | `client(url, method='PUT', ...)` |
| `.delete(...)`  | `client(url, method='DELETE', ...)` |
| `.option(...)`  | `client(url, method='OPTION', ...)` |

所有方法均支持以下参数：
- `url`: 请求地址
- `params`: 参数（GET 查询参数 或 POST 表单数据）
- `headers`: 自定义头部
- `files`: 文件上传（仅 POST/PUT 有效）
- `stream`: 是否流式接收

---

## 使用示例

### 基本 GET 请求
```python
client = Http_Client()
data = client.get("https://api.example.com/users")
print(data)
```

### POST 提交表单
```python
payload = {"username": "admin", "password": "123456"}
resp = client.post("https://api.example.com/login", params=payload)
```

### 上传文件
```python
files = {'file': open('report.pdf', 'rb')}
resp = client.post("https://api.example.com/upload", files=files)
```

### 流式下载大文件
```python
resp = client.get("https://example.com/large-file.zip", stream=True)
with open("download.zip", "wb") as f:
    for chunk in resp.iter_content(1024):
        f.write(chunk)
```

### 异常捕获
```python
try:
    data = client.get("https://api.example.com/secure-data")
except NeedLogin:
    print("请先登录")
except InsufficientPrivilege:
    print("权限不足")
except HTTPError as e:
    print(f"HTTP 错误: {e}")
```

---

## 注意事项与改进建议

1. **SSL 验证关闭**  
   `self.s.verify = False` 存在安全风险，建议增加配置项控制是否关闭验证。

2. **`__expr__` 应为 `__repr__`**  
   当前 `HTTPError.__expr__` 方法不会被 Python 调用，请更正为 `__repr__`。

3. **Session Key 名称硬编码**  
   当前假设 Cookie 中第一个字段是 session ID，实际中可能需根据具体服务调整（如 `JSESSIONID`, `token` 等）。

4. **并发安全性**  
   `hostsessions` 是全局共享字典，在多线程环境下可能存在竞争条件，建议加锁或使用线程局部存储。

5. **缺少超时设置**  
   推荐在 `send()` 调用中添加 `timeout` 参数防止无限等待。

6. **headers 更新影响原始输入**  
   `headers.update(...)` 修改了传入的字典，建议复制一份再操作。

---

## 版本信息

- 编写语言：Python 3.x
- 第三方依赖：`requests >= 2.20.0`
- 许可：MIT（示例代码，实际项目需明确授权）

--- 

✅ 本库适合快速集成 RESTful API 调用，具备良好的扩展性和清晰的异常体系。