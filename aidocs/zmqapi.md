# ZeroMQ 异步通信模块技术文档

本模块基于 `zmq.asyncio` 提供了一组用于构建异步消息通信系统的 Python 类，支持多种 ZeroMQ 模式：**发布/订阅 (Pub/Sub)**、**请求/响应 (Req/Rep)**、**推/拉 (Push/Pull)** 和 **对等连接 (Pair)**。所有类均为异步设计，适用于 `asyncio` 协程环境。

---

## 📦 依赖

- Python 3.7+
- `pyzmq`（`pip install pyzmq`）
- `asyncio`

> 注意：使用前请确保已安装 `pyzmq` 并支持 `asyncio` 集成。

```bash
pip install pyzmq
```

---

## 🧩 核心功能概览

| 类名         | 功能描述                         | ZeroMQ 模式 |
|--------------|----------------------------------|-------------|
| `Publisher`  | 发布消息到多个订阅者             | PUB         |
| `Subscriber` | 订阅特定消息 ID 的消息           | SUB         |
| `RRServer`   | 请求-响应模式的服务端            | REP         |
| `RRClient`   | 请求-响应模式的客户端            | REQ         |
| `PPPusher`   | 推送任务或数据                   | PUSH        |
| `PPPuller`   | 拉取并处理任务或数据             | PULL        |
| `PairClient` | 点对点双向通信客户端             | PAIR        |
| `PairServer` | 点对点双向通信服务端（可带处理器）| PAIR        |

---

## 🔧 使用说明与 API 文档

### 1. `Publisher` - 发布者（PUB）

用于向多个订阅者广播消息。

#### ✅ 初始化

```python
pub = Publisher(port, coding='utf-8', msgid=1000)
```

- `port`: int，绑定的 TCP 端口。
- `coding`: str，默认 `'utf-8'`，编码格式。
- `msgid`: int，默认 `1000`，默认消息 ID 前缀。

#### 📡 方法：`publish(msg, msgtype='text', msgid=-1)`

发送一条消息。

- `msg`: 要发送的内容（字符串或可序列化对象）。
- `msgtype`: 消息类型，支持 `'text'` 或其他如 `'json'`。
- `msgid`: 自定义消息 ID，若为 `-1` 则使用实例默认值。

> 若 `msgtype != 'text'`，会自动将 `msg` 通过 `json.dumps()` 序列化，并强制设为 `'json'` 类型。

##### 示例：
```python
await pub.publish("Hello World")
await pub.publish({"data": 42}, msgtype="json")
```

##### 消息格式（在传输中）：
```
<msgid> <msgtype> <body>
```

例如：
```
1000 json {"data": 42}
```

#### 💡 注意事项
- 多个订阅者可通过不同端口连接同一发布者。
- 不保证消息送达（ZMQ PUB/SUB 特性）。

---

### 2. `Subscriber` - 订阅者（SUB）

接收来自一个或多个发布者的特定消息。

#### ✅ 初始化

```python
sub = Subscriber(host, ports, msgid, coding='utf-8')
```

- `host`: str，发布者主机地址（如 `'localhost'`）。
- `ports`: list of int，要连接的一个或多个端口。
- `msgid`: int，只订阅以该 ID 开头的消息。
- `coding`: str，解码方式，默认 `'utf-8'`。

> 内部设置 `SUBSCRIBE` 过滤器为 `b'<msgid>'`，仅接收匹配前缀的消息。

#### ➕ 方法：`addPort(port)`

动态添加一个新的发布者端口进行连接。

```python
sub.addPort(5556)
```

#### 📥 方法：`subscribe() → str or dict`

异步接收并解析下一条消息。

- 返回值：
  - 若 `msgtype == 'json'`：返回反序列化的 `dict`。
  - 否则返回原始字符串。

##### 示例：
```python
data = await sub.subscribe()
print(data)  # 可能是字符串或字典
```

#### 💡 注意事项
- 必须确保发布的 `msgid` 与订阅者设置的一致才能接收到消息。
- 支持多播场景，可同时连接多个发布者端口。

---

### 3. `RRServer` - 请求/响应服务端（REP）

实现同步式的请求-应答服务器。

#### ✅ 初始化

```python
server = RRServer(port, handler=None)
```

- `port`: int，监听端口。
- `handler`: callable，可选回调函数，处理请求并返回响应。
  - 支持普通函数和 `async def` 协程。

#### ▶️ 方法：`run()`

启动服务循环，持续监听请求。

##### 处理逻辑：
1. 接收请求消息 `rmsg`（bytes）。
2. 若有 `handler`，调用它生成响应 `wmsg`。
3. 如果 `handler` 返回的是协程，则等待其完成。
4. 将响应发回客户端。

##### 示例 Handler：
```python
def my_handler(msg):
    return b"Echo: " + msg

# 或异步版本
async def async_handler(msg):
    await asyncio.sleep(0.1)
    return b"Processed"
```

##### 启动服务：
```python
await server.run()
```

> ⚠️ 此方法为无限循环，需运行在事件循环中。

---

### 4. `RRClient` - 请求/响应客户端（REQ）

向 `RRServer` 发起请求并等待响应。

#### ✅ 初始化

```python
client = RRClient(host, port)
```

- `host`: str，服务器地址。
- `port`: int，服务器端口。

#### 📤 方法：`request(msg) → bytes`

发送请求并返回响应。

```python
response = await client.request(b"Hello")
print(response)  # b'Echo: Hello'
```

> REQ/REP 是严格的一问一答模式，不能连续两次发送。

---

### 5. `PPPusher` - 推送器（PUSH）

用于向一个或多个 `PPPuller` 推送任务或消息。

#### ✅ 初始化

```python
pusher = PPPusher(host, port)
```

- `host`: 绑定的 IP 地址（通常 `'*'` 或 `'localhost'`）。
- `port`: 绑定端口。

> 使用 `PUSH` 模式，适合负载均衡分发任务。

#### 🚀 方法：`push(msg)`

推送一条消息（bytes 或字符串需编码）。

```python
await pusher.push(b"Task 1")
```

---

### 6. `PPPuller` - 拉取器（PULL）

从 `PPPusher` 接收消息并处理。

#### ✅ 初始化

```python
puller = PPPuller(host, port, handler=None)
```

- `host`: 监听地址。
- `port`: 监听端口。
- `handler`: 接收到消息后的处理函数（可为协程）。

#### ▶️ 方法：`run()`

启动拉取循环，持续接收消息并交由 `handler` 处理。

```python
async def handle_task(msg):
    print("Processing:", msg)

puller = PPPuller('localhost', 5558, handle_task)
await puller.run()
```

> 支持异步处理器，自动 `await` 协程结果。

---

### 7. `PairClient` - 对等客户端（PAIR）

实现简单的点对点双向通信中的“客户端”角色。

#### ✅ 初始化

```python
client = PairClient(host, port)
```

- `host`: 连接目标 IP。
- `port`: 连接端口。

> 实际上是主动 `bind` 的一方，在 PAIR 模式中双方只能一对一。

#### 📤 方法：`request(msg) → bytes`

发送消息并等待对方回复。

```python
resp = await client.request(b"Ping")
```

---

### 8. `PairServer` - 对等服务端（PAIR）

接收来自 `PairClient` 的消息并响应。

#### ✅ 初始化

```python
server = PairServer(port, handler=None)
```

- `port`: 监听端口。
- `handler`: 处理函数，决定返回内容（支持协程）。

#### ▶️ 方法：`run()`

开启监听循环：

```python
async def echo_handler():
    return b"OK"

server = PairServer(5560, echo_handler)
await server.run()
```

> PAIR 模式不支持多客户端，仅用于两个节点间的直接通信。

---

## 🔄 通信模式对比

| 模式       | 典型用途               | 特点 |
|------------|------------------------|------|
| PUB/SUB    | 广播通知、事件流       | 多播，无确认，可能丢包 |
| REQ/REP    | 同步远程调用           | 严格同步，一问一答 |
| PUSH/PULL  | 工作队列、任务分发     | 流水线架构，支持扇出 |
| PAIR       | 点对点控制信道         | 简单双向通信，限一对一双向 |

---

## 🧪 示例：简单发布/订阅

```python
# publisher.py
import asyncio
from your_module import Publisher

async def main():
    pub = Publisher(5555)
    while True:
        await pub.publish("Hi there!", msgtype="text")
        await asyncio.sleep(1)

asyncio.run(main())
```

```python
# subscriber.py
import asyncio
from your_module import Subscriber

async def main():
    sub = Subscriber('localhost', [5555], msgid=1000)
    while True:
        msg = await sub.subscribe()
        print("Received:", msg)

asyncio.run(main())
```

---

## ⚠️ 注意事项与最佳实践

1. **资源释放**：
   - 所有类在析构时自动关闭 socket，但仍建议显式管理生命周期。
   - 避免未关闭上下文导致文件描述符泄漏。

2. **消息过滤（SUB）**：
   - ZeroMQ SUB 的订阅是基于前缀匹配的字节流。
   - 当前实现使用 `setsockopt(zmq.SUBSCRIBE, b'1000')`，只会收到以 `1000` 开头的消息。

3. **编码一致性**：
   - 发送与接收方必须使用相同编码（默认 UTF-8）。

4. **异步处理器兼容性**：
   - `RRServer`、`PPPuller`、`PairServer` 均支持同步和异步处理器。
   - 使用 `isinstance(x, Coroutine)` 判断是否需要 `await`。

5. **错误处理建议**：
   - 生产环境中应在 `try-except` 中包裹 `recv()` 和 `send()` 操作。
   - 添加超时机制防止阻塞。

6. **性能提示**：
   - 使用 `context = zmq.asyncio.Context.instance()` 可共享上下文实例提升效率。

---

## 📚 扩展建议

- 添加日志输出替代 `print()`。
- 增加心跳、重连机制。
- 支持 TLS 加密传输。
- 提供更高级的消息封装协议（如带时间戳、来源标识等）。

---

## 📎 版本信息

- 编写日期：2025年4月5日
- 作者：AI Assistant
- 许可：MIT（假设代码开源）

--- 

📌 **提示**：将此模块保存为 `zmq_async.py`，即可导入使用：

```python
from zmq_async import Publisher, Subscriber, ...
```