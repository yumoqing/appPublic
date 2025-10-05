# `HttpClient` 与 `JsonHttpAPI` 技术文档

---

## 概述

本文档介绍了一个基于 `aiohttp` 的异步 HTTP 客户端库，包含两个核心类：

- `HttpClient`：提供灵活、可配置的异步 HTTP 请求功能，支持代理（SOCKS5）、自动重试、Cookie 管理、域名黑名单缓存等。
- `JsonHttpAPI`：构建在 `HttpClient` 上的高级接口，用于处理 JSON 格式的 API 调用，支持模板渲染、流式响应处理和动态参数注入。

该模块适用于需要高并发访问 Web 接口、支持代理切换、具备容错机制的应用场景。

---

## 依赖项

```txt
aiohttp
aiohttp_socks
certifi
ssl
asyncio
urllib.parse
json
re
traceback
os
appPublic.myTE (自定义模板引擎)
appPublic.log (日志模块)
```

> 注意：`appPublic.*` 是项目内部工具模块，请确保已安装或替换为对应实现。

---

## 全局常量

| 常量 | 值 | 含义 |
|------|----|------|
| `RESPONSE_BIN`   | `0` | 返回二进制数据（`bytes`） |
| `RESPONSE_TEXT`  | `1` | 返回文本字符串（使用编码解码） |
| `RESPONSE_JSON`  | `2` | 返回解析后的 JSON 对象 |
| `RESPONSE_FILE`  | `3` | 预留，表示文件下载（当前未使用） |
| `RESPONSE_STREAM`| `4` | 流式传输模式（通过 `__call__` 实现） |

---

## 工具函数

### `get_domain(url: str) -> str`

从 URL 中提取域名（主机名），若 URL 不带协议则默认补全为 `http://`。

#### 参数：
- `url` (str): 输入的 URL 字符串。

#### 返回值：
- `str`: 提取出的域名部分（不包含端口和路径）。

#### 示例：
```python
get_domain("https://example.com:8080/path") → "example.com"
get_domain("example.org") → "example.org" （自动补全 http）
```

---

## 异常类

### `HttpError(code, msg)`

继承自 `Exception`，表示 HTTP 请求失败时的错误。

#### 属性：
- `code` (int): HTTP 状态码。
- `msg` (str): 错误描述信息。

#### 方法：
- `__str__()`: 返回格式化错误信息 `"Error Code:{code}, {msg}"`。
- `__expr__()`: 同 `__str__()`，兼容调试输出。

---

## 核心类：`HttpClient`

一个异步 HTTP 客户端，支持 SOCKS5 代理、自动故障转移、Cookie 管理及域名黑名单持久化。

### 初始化：`__init__(coding='utf-8', socks5_proxy_url=None)`

#### 参数：
- `coding` (str): 文本响应的字符编码，默认 `'utf-8'`。
- `socks5_proxy_url` (str or None): 可选的 SOCKS5 代理地址，如 `'socks5://localhost:1086'`。

#### 内部状态：
- `session`: `aiohttp.ClientSession` 实例（延迟初始化）。
- `cookies`: 存储各域名 Cookie 的字典。
- `proxy_connector`: 当前使用的代理连接器。
- `blocked_domains`: 被标记为无法直连需走代理的域名集合（从 `.proxytarget` 文件加载）。
- `load_cache()`: 自动加载本地缓存的被屏蔽域名列表。

---

### 方法说明

#### `save_cache()`
将当前 `blocked_domains` 集合保存到用户主目录下的 `~/.proxytarget` 文件中，每行一个域名。

#### `load_cache()`
从 `~/.proxytarget` 加载被屏蔽域名。如果文件不存在，则创建空文件。

#### `close()`
关闭当前会话（释放资源），协程方法。

#### `setCookie(url, cookies)`
根据 URL 设置对应域名的 Cookie。

#### `getCookies(url)`
获取指定 URL 所属域名的 Cookies。

#### `getsession(url)`
懒加载并返回 `ClientSession` 实例，启用 `unsafe=True` 的 CookieJar 以接受任意域的 Cookie。

#### `response_generator(url, resp)`
生成器函数，逐块返回响应内容（每次最多 1024 字节），同时更新 Cookie。

#### `response_handle(url, resp, resp_type, stream_func)`
根据 `resp_type` 类型处理响应体，并可选地调用 `stream_func` 处理流式数据。

| `resp_type`       | 行为 |
|-------------------|------|
| `RESPONSE_BIN`    | `await resp.read()` |
| `RESPONSE_TEXT`   | `await resp.text(encoding)` |
| `RESPONSE_JSON`   | `await resp.json()` |
| 其他 / `None`     | 忽略 |

若提供了 `stream_func`，则以 chunk 方式流式传递数据。

#### `grapCookie(url)`
从当前 Session 的 CookieJar 中提取特定域名的所有 Cookie。

#### `make_request(...)`
底层请求构造函数，支持 GET/POST 等方法，允许传入 `params`, `data`, `jd`（JSON 数据）、`headers`。

##### 参数：
- `url`: 请求地址。
- `method`: HTTP 方法（GET、POST 等）。
- `params`: 查询参数（dict）。
- `data`: 表单数据（bytes 或 dict）。
- `jd`: JSON 数据（会被设置为 `json=` 参数）。
- `headers`: 请求头。
- `use_proxy`: 是否使用 SOCKS5 代理。

> 若是 HTTPS 请求，自动添加由 `certifi` 提供的 CA 证书上下文。

#### `get_request_response(...)`
智能路由请求：先尝试直连；若失败且存在代理配置，则记录失败域名并改用代理重试。

##### 特性：
- 自动检测是否应绕过代理（不在 `blocked_domains` 中）。
- 第一次请求失败后，将域名加入 `blocked_domains` 并持久化。
- 支持异常捕获与日志输出。

#### `request(...)`
高层封装，发送请求并按 `response_type` 解析结果。

##### 参数：
- `response_type`: 控制返回类型（见全局常量）。
- `stream_func`: 可选的异步回调函数，用于处理流式数据块。
- 其余同 `make_request`。

##### 返回：
- 成功时返回相应类型的响应数据。
- 失败时抛出 `HttpError`。

#### `__call__(...)`
支持 `async for` 的流式调用方式，适合大文件下载或 Server-Sent Events 场景。

##### 示例：
```python
async for chunk in hc('https://example.com/stream'):
    print(chunk)
```

#### `get(url, **kw)` 和 `post(url, **kw)`
便捷方法，分别发起 GET 和 POST 请求。

---

## 高级类：`JsonHttpAPI`

专为调用 RESTful JSON API 设计的模板驱动客户端。

### 初始化：`__init__(env={}, socks5_proxy_url=None)`

#### 参数：
- `env` (dict): 全局变量环境，供模板渲染使用。
- `socks5_proxy_url` (str): 传递给底层 `HttpClient` 的代理设置。

#### 内部组件：
- `te`: 使用 `MyTemplateEngine` 进行模板渲染。
- `hc`: 实例化的 `HttpClient`。

---

### 方法说明

#### `stream_func(chunk)`
内部流处理器，用于处理换行分隔的 JSON 流（如 SSE）。**注意：代码中有拼写错误 `chuck` 应为 `chunk`**。

> ⚠️ Bug 提示：原代码中 `d = self.chunk_buffer + chuck` 应改为 `chunk`。

功能包括：
- 缓冲数据并按 `\n` 分割。
- 尝试解析每条 JSON 消息。
- 使用 `resptmpl` 渲染响应。
- 调用用户提供的 `user_stream_func` 回调。

#### `chunk_handle(chunk, lead, end)`
钩子函数，可用于预处理每个数据块（例如去除前缀、添加结束标记）。默认直接返回原块。

#### `__call__(...)`
异步生成器接口，支持流式 API 调用。

##### 参数：
- `url`: API 地址。
- `method`: 请求方法。
- `ns`: 当前命名空间变量（优先级高于 `env`）。
- `headerstmpl`: 请求头的 JSON 模板（字符串形式的 JSON + 模板语法）。
- `paramstmpl`: 查询参数模板。
- `datatmpl`: 请求体模板（JSON 字符串含变量）。
- `chunk_leading`, `chunk_end`: 分块控制标记。
- `resptmpl`: 响应数据的输出模板。

##### 流程：
1. 合并 `env` 与 `ns` 得到上下文。
2. 渲染各个模板（headers/params/data）。
3. 发起流式请求。
4. 分块处理响应，可结合 `resptmpl` 动态转换输出。

##### 输出：
- `yield` 经过处理和模板渲染后的每一“段”数据。

#### `call(...)`
同步风格的调用入口（实际仍是 `await` 协程），支持非流式和流式两种模式。

##### 参数：
- `stream_func`: 用户自定义流处理函数（接收 JSON 对象）。
- 其他同 `__call__`。

##### 返回：
- 若无 `resptmpl`：原始 JSON 响应。
- 若有 `resptmpl`：经模板渲染后再反序列化的 JSON 结果。

---

## 使用示例

### 1. 基础请求（主程序测试）

```python
async def main():
    hc = HttpClient(socks5_proxy_url='socks5://localhost:1086')
    
    # 流式读取百度首页
    async for d in hc('https://www.baidu.com'):
        print(d)

    # 获取 Google 主页文本
    r = await hc.request('https://www.google.com')
    print(r)

    await hc.close()

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
```

### 2. 使用 `JsonHttpAPI` 调用模板化 API

```python
api = JsonHttpAPI(env={'token': 'abc123'}, socks5_proxy_url='socks5://127.0.0.1:1086')

# 定义模板
headers_tmpl = '{"Authorization": "Bearer {{token}}"}'
params_tmpl = '{"page": "{{page}}"}'

async def on_chunk(data):
    print("Received:", data)

result = await api.call(
    url="https://api.example.com/data",
    method="GET",
    ns={"page": 1},
    headerstmpl=headers_tmpl,
    paramstmpl=params_tmpl,
    stream_func=on_chunk
)
```

---

## 注意事项与建议

### ✅ 优点
- 支持异步高并发。
- 内建代理自动切换机制。
- Cookie 自动管理。
- 模板化请求构建，适合复杂 API 集成。
- 黑名单域名持久化，避免重复探测。

### ❗ 已知问题 / 改进建议

1. **Bug：`stream_func` 中 `chuck` 拼写错误**
   ```python
   d = self.chunk_buffer + chuck  # 应为 chunk
   ```

2. **`jd` 参数未正确使用**
   - 在 `make_request` 中设置了 `hp['jd'] = jd`，但 `aiohttp.request()` 不识别 `jd`。
   - 应改为 `hp['json'] = jd`。

3. **`datatmpl` 中 multipart 注释未启用**
   - 当前行被注释，导致无法上传文件。
   - 如需支持 form-data，应取消注释并修复逻辑。

4. **`chunk_handle` 接口设计模糊**
   - 当前仅作占位，建议明确其用途（如过滤、转换、拼接等）。

5. **安全性考虑**
   - `unsafe=True` 的 CookieJar 可能带来安全风险，建议限制作用域。
   - 模板渲染可能引入注入风险，建议对输入做校验。

6. **日志级别使用建议**
   - `info(f'{headers=}...')` 输出敏感信息（如 token），建议降级为 `debug`。

---

## 总结

本模块是一个功能完整的异步 HTTP 客户端解决方案，特别适用于以下场景：

- 需要通过 SOCKS5 代理访问受限资源。
- 面向多个 JSON API 的自动化集成。
- 支持流式响应（如聊天机器人、事件流）。
- 具备一定的容错和自适应能力。

配合模板引擎，可以实现高度可配置的 API 调用系统，适合作为微服务网关、爬虫框架或自动化测试工具的基础组件。

---

## 版本信息

- 作者：未知
- 最后修改时间：根据代码推断为近期开发
- 兼容性：Python 3.7+

> 建议增加版本号字段和单元测试覆盖。

--- 

✅ **文档完成**