以下是为提供的 `OAuthClient` 类编写的 **Markdown 格式技术文档**，涵盖了类的功能、设计思想、使用方式、参数说明及示例等内容。

---

# `OAuthClient` 技术文档

`OAuthClient` 是一个基于 HTTP(S) 的异步客户端工具类，用于调用由第三方服务发布的 RESTful API 接口。它通过预定义的接口描述（`desc`）动态构建请求，并解析响应数据，支持自定义数据转换、错误判断逻辑和返回结构处理。

该类广泛应用于需要与 OAuth 认证或标准 JSON API 交互的服务中，具有良好的可配置性和扩展性。

---

## 📦 模块依赖

```python
import json
from appPublic.httpclient import HttpClient, RESPONSE_TEXT, RESPONSE_JSON, RESPONSE_BIN, RESPONSE_FILE, RESPONSE_STREAM, HttpError
from appPublic.argsConvert import ArgsConvert
from appPublic.dictObject import DictObject
```

- `HttpClient`: 异步 HTTP 客户端，支持多种响应类型。
- `ArgsConvert`: 用于模板字符串替换（如 `${key}`）。
- `DictObject`: 支持通过属性访问字典键值的对象封装。

---

## 🧱 类定义

```python
class OAuthClient:
    def __init__(self, desc, converters={})
```

### 构造函数参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `desc` | `dict` | 接口描述对象，必须包含 `data` 字段，定义了基础数据和各 API 方法的配置。详见下方“接口描述格式”章节。 |
| `converters` | `dict[str, callable]` | 可选的数据转换函数映射表，键为转换器名称，值为函数引用。 |

> ⚠️ 注意：`desc['data']` 必须存在，否则会抛出断言错误。

---

## 🔧 接口描述格式 (`desc`)

`desc` 是一个字典，其结构如下：

```json
{
  "data": { /* 基础共享数据，可在请求时被引用 */ },
  "method_name": {
    "path": "/api/v1/users/${userId}",
    "method": "GET",  // 可选，默认 GET
    "headers": [ ... ],
    "params": [ ... ],
    "data": [ ... ],  // 请求体中的数据
    "resp": [
      {
        "name": "result",
        "resp_keys": ["user", "name"],
        "converter": "to_upper"  // 可选
      }
    ],
    "error_if": {
      "error_keys": ["status"],
      "op": "==",           // 比较操作符：'==' 或 '!='
      "value": "fail",
      "code_keys": ["code"], // 错误码路径
      "msg_keys": ["message"] // 错误信息路径
    }
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `data` | `dict` | 全局上下文数据，可用于模板替换。 |
| `method_name` | `dict` | 每个 API 接口的配置项，方法名作为 key。 |
| &nbsp;&nbsp;`path` | `str` | 接口路径，支持 `${}` 占位符变量。 |
| &nbsp;&nbsp;`method` | `str` | HTTP 方法（GET/POST/PUT/DELETE 等），默认为 `GET`。 |
| &nbsp;&nbsp;`headers` | `list[dict]` | 请求头列表，每个元素形如 `{name: "Header-Key", value: "HeaderValue", converter?: "funcName"}` |
| &nbsp;&nbsp;`params` | `list[dict]` | URL 查询参数，格式同上。 |
| &nbsp;&nbsp;`data` | `list[dict]` | 请求体数据（JSON 格式），格式同上。 |
| &nbsp;&nbsp;`resp` | `list[dict]` | 响应数据提取规则。 |
| &nbsp;&nbsp;&nbsp;&nbsp;`name` | `str` | 返回结果中字段的名称。 |
| &nbsp;&nbsp;&nbsp;&nbsp;`resp_keys` | `list[str]` | 在响应 JSON 中获取数据的路径（嵌套键）。 |
| &nbsp;&nbsp;&nbsp;&nbsp;`converter` | `str` | 转换函数名（需在 `converters` 中注册）。 |
| &nbsp;&nbsp;`error_if` | `dict` | 自定义错误判断条件。 |
| &nbsp;&nbsp;&nbsp;&nbsp;`error_keys` | `list[str]` | 提取用于比较的响应字段路径。 |
| &nbsp;&nbsp;&nbsp;&nbsp;`op` | `str` | 比较操作符：`==` 或 `!=`。 |
| &nbsp;&nbsp;&nbsp;&nbsp;`value` | any | 期望值，用于对比。 |
| &nbsp;&nbsp;&nbsp;&nbsp;`code_keys` | `list[str]` | 错误码字段路径（可选）。 |
| &nbsp;&nbsp;&nbsp;&nbsp;`msg_keys` | `list[str]` | 错误消息字段路径（可选）。 |

---

## 🧩 核心方法

### `__call__(self, host, mapi, params) -> dict`

发起一次 API 调用。

#### 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `host` | `str` | 服务主机地址，例如 `"https://api.example.com"` |
| `mapi` | `str` | 接口方法名，对应 `desc` 中的键名。 |
| `params` | `dict` | 动态传入的参数，用于替换模板和构造请求。 |

#### 返回值

成功时：
```json
{
  "status": "ok",
  "data": { /* 根据 resp 配置提取的数据 */ }
}
```

失败时：
```json
{
  "status": "error",
  "code": "400",
  "message": "Bad Request"
}
```

#### 流程说明

1. 查找 `desc[mapi]` 是否存在；
2. 使用 `datalize()` 替换路径中的 `${}` 变量；
3. 构造完整 URL；
4. 处理 headers、params、data（应用转换器）；
5. 发起异步 HTTP 请求；
6. 解析响应为 `DictObject`；
7. 检查是否符合 `error_if` 条件；
8. 按照 `resp` 规则提取并转换返回数据。

> 📌 日志输出：请求详情（URL、method、params 等）将打印到控制台。

---

### `setup_req_data(data, ns) -> dict or None`

将一组 `{name, value, converter}` 结构的数据根据命名空间 `ns` 进行模板替换和转换。

#### 参数

- `data`: 数据项列表（如 headers、params）
- `ns`: 命名空间（通常是 `params`）

#### 内部调用

- `setup_req_kv()`: 处理单个键值对，执行模板替换和转换。

---

### `datalize(dic, data={}) -> dict`

执行模板替换（`${key}` → 实际值）。

#### 说明

- 合并 `self.data`（全局数据）与传入的 `data`；
- 使用 `ArgsConvert('${', '}')` 执行替换；
- 支持嵌套字典和字符串。

#### 示例

```python
self.data = {'token': 'abc123'}
dic = {'url': '/api?tk=${token}'}
result = self.datalize(dic)  # {'url': '/api?tk=abc123'}
```

---

### `get_resp_data(resp, keys, converter=None)`

从响应对象中按 `keys` 路径提取数据，并可选地进行转换。

#### 参数

- `resp`: `DictObject` 类型的响应体；
- `keys`: 键路径列表，如 `['data', 'user', 'id']`；
- `converter`: 转换函数名。

#### 示例

```python
resp = DictObject(data={"user": {"name": "alice"}})
value = get_resp_data(resp, ['data', 'user', 'name'])  # "alice"
```

---

### `setup_return_data(resp) -> dict`

根据 `api.resp` 配置，构建最终返回的 `data` 对象。

#### 示例配置

```json
"resp": [
  {
    "name": "username",
    "resp_keys": ["data", "user", "name"],
    "converter": "to_upper"
  }
]
```

#### 输出

```json
{
  "status": "ok",
  "data": {
    "username": "ALICE"
  }
}
```

---

### `check_if_error(resp) -> dict or None`

检查响应是否满足预设的错误条件。

#### 判断逻辑

```python
v = resp.get_data_by_keys(ei.error_keys)
if ei.op == '==' and v == ei.value → 触发错误
if ei.op == '!=' and v != ei.value → 触发错误
```

#### 成功返回

- `None` 表示无错误。

#### 失败返回

```json
{
  "status": "error",
  "code": "...",
  "message": "..."
}
```

> 💡 支持从响应中提取 `code` 和 `message`。

---

### `set_data(resp_data, data_desc)`

将响应中的某些字段保存回 `self.data`，用于后续请求共享状态（如 token 刷新）。

#### 参数

- `resp_data`: 原始响应数据（dict）
- `data_desc`: 描述如何映射字段

```python
data_desc = [
    {'field': 'access_token', 'name': 'token'},
    {'field': 'expires_in', 'name': 'expires'}
]
```

执行后：
```python
self.data['token'] = resp_data['access_token']
self.data['expires'] = resp_data['expires_in']
```

---

## ✅ 使用示例

### 1. 定义接口描述

```python
desc = {
    "data": {
        "client_id": "your_client_id",
        "client_secret": "your_secret"
    },
    "get_user": {
        "path": "/users/${user_id}",
        "method": "GET",
        "headers": [
            {"name": "Authorization", "value": "Bearer ${token}"}
        ],
        "resp": [
            {
                "name": "userInfo",
                "resp_keys": ["data"],
                "converter": "strip_data"
            }
        ],
        "error_if": {
            "error_keys": ["status"],
            "op": "==",
            "value": "error",
            "code_keys": ["error_code"],
            "msg_keys": ["error_msg"]
        }
    }
}
```

### 2. 定义转换器

```python
def to_upper(s):
    return s.upper() if isinstance(s, str) else s

converters = {
    "to_upper": to_upper,
    "strip_data": lambda x: x.get('data') if isinstance(x, dict) else x
}
```

### 3. 创建并调用客户端

```python
client = OAuthClient(desc, converters=converters)

result = await client(
    host="https://api.example.com",
    mapi="get_user",
    params={
        "user_id": "123",
        "token": "xyz987"
    }
)

print(result)
# 输出:
# {
#   "status": "ok",
#   "data": {
#     "userInfo": { ... }
#   }
# }
```

---

## 🛠️ 调试信息

所有请求细节将通过 `print()` 输出：

```python
print(f'{url=}, {method=}, {myparams=}, {mydata=}, {myheaders=}')
```

建议在生产环境中移除或替换为日志记录。

---

## ❗ 异常处理

- 若指定的 `mapi` 未在 `desc` 中定义，抛出 `Exception`；
- HTTP 请求异常捕获为 `HttpError`，返回标准错误结构；
- 网络级错误（如连接超时）也会被捕获并返回 `"https error"`。

---

## 🧩 扩展建议

- 添加日志模块替代 `print()`；
- 支持更多响应类型（如文件下载）；
- 增加中间件钩子（before_request / after_response）；
- 支持分页自动迭代。

---

## 📚 总结

`OAuthClient` 是一个灵活、声明式的 API 客户端封装，适用于微服务间通信、第三方接口集成等场景。通过配置驱动的方式，实现了解耦与复用，适合构建统一的外部服务网关层。

--- 

> 📎 版本：1.0  
> 📅 最后更新：2025年4月5日  
> © 2025 Your Company. All rights reserved.