# ZMQ Request-Reply 模块技术文档

`zmq_reqresp.py` 是一个基于 ZeroMQ 的请求-响应（Request-Response）通信模式的 Python 封装模块，支持同步与异步两种运行模式。该模块提供了 `ZmqRequester` 和 `ZmqReplier` 两个核心类，分别用于客户端发送请求和服务器端接收并回复请求。

---

## 目录

- [概述](#概述)
- [依赖](#依赖)
- [类说明](#类说明)
  - [`ZmqRequester`](#zmqrqester)
  - [`ZmqReplier`](#zmqreplier)
- [使用示例](#使用示例)
  - [同步模式示例](#同步模式示例)
  - [异步模式示例](#异步模式示例)
- [异常处理](#异常处理)
- [注意事项](#注意事项)

---

## 概述

本模块封装了 ZeroMQ 的 `REQ/REP` 套接字模式，实现了：
- 支持字符串和字节流的消息传输；
- 同步与异步双模式支持；
- 可配置超时重连机制；
- 简洁易用的 API 接口。

适用于构建轻量级远程调用、微服务间通信等场景。

---

## 依赖

```txt
pyzmq >= 22.0
Python >= 3.7
```

> 注：异步功能依赖于 `asyncio` 和 `zmq.asyncio`。

---

## 类说明

### `ZmqRequester`

代表一个 ZeroMQ 客户端（REQ 套接字），用于向服务端发送请求并接收响应。

#### 初始化参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `url` | str | 连接的服务端地址，如 `"tcp://127.0.0.1:5555"` |
| `async_mode` | bool | 是否启用异步模式，默认为 `False` |
| `timeout` | int | 接收响应的超时时间（单位：秒），设为 0 表示阻塞等待 |

> ⚠️ 若 `timeout > 0`，内部会使用 `Poller` 实现非阻塞轮询，并在超时时自动重连。

#### 方法

##### `send(msg: str) -> str or None`
- **描述**：同步发送字符串消息，返回响应字符串。
- **参数**：
  - `msg`: 要发送的字符串（UTF-8 编码）
- **返回值**：服务端返回的字符串，或 `None`（超时）
- **异常**：若处于异步模式则抛出异常

##### `send_b(b: bytes) -> bytes or None`
- **描述**：同步发送字节数据，返回字节响应。
- **参数**：
  - `b`: 要发送的字节对象
- **返回值**：响应字节数据，或 `None`（超时）

##### `async asend(msg: str) -> str or None`
- **描述**：异步发送字符串消息。
- **参数**：
  - `msg`: 字符串消息
- **返回值**：响应字符串或 `None`
- **异常**：若未启用异步模式则抛出异常

##### `async asend_b(b: bytes) -> bytes or None`
- **描述**：异步发送字节数据。
- **参数**：
  - `b`: 字节数据
- **返回值**：响应字节数据或 `None`

##### `_connect()`
- 内部方法，用于创建上下文并连接到服务端。

##### `_close()`
- 内部方法，关闭套接字和上下文资源。

> ✅ 自动在析构函数中调用 `_close()` 释放资源。

---

### `ZmqReplier`

代表一个 ZeroMQ 服务端（REP 套接字），监听请求并调用处理器函数进行响应。

#### 初始化参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `url` | str | 绑定地址，如 `"tcp://*:5555"` |
| `handler` | callable 或 coroutine function | 处理请求的回调函数 |
| `async_mode` | bool | 是否以异步模式运行 |

> ⚠️ 若 `async_mode=False`，但 `handler` 是协程函数，则会抛出错误。

#### 回调函数要求

- 输入：`bytes` 类型的请求数据
- 输出：可为 `bytes` 或 `str`（自动编码为 UTF-8）

#### 方法

##### `run()`
- **描述**：启动服务端（同步模式）
- **行为**：在后台线程中运行 `_run()`，不阻塞主线程
- 使用 `Background` 类实现多线程执行

##### `async_run()`
- **描述**：异步运行服务端主循环（需在事件循环中 await）
- **注意**：此方法不会自动启动任务，需手动调度至 `asyncio` 事件循环

##### `_run()`
- 同步主循环逻辑：接收请求 → 调用处理器 → 发送响应

##### `stop()`
- **描述**：停止服务端运行
- 设置 `keep_running = False` 并尝试 `join()`（注：当前 `join()` 未定义，见[注意事项](#注意事项)）

---

## 使用示例

### 同步模式示例

#### 服务端（Replier）

```python
def echo_handler(data: bytes) -> bytes:
    return b"Echo: " + data

replier = ZmqReplier("tcp://*:5555", echo_handler, async_mode=False)
replier.run()

# 主程序保持运行
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    replier.stop()
```

#### 客户端（Requester）

```python
req = ZmqRequester("tcp://127.0.0.1:5555", async_mode=False, timeout=5)
response = req.send("Hello")
print(response)  # 输出: Echo: Hello
```

---

### 异步模式示例

#### 异步服务端

```python
import asyncio

async def async_handler(data: bytes) -> bytes:
    await asyncio.sleep(0.1)  # 模拟异步操作
    return b"Async reply to " + data

replier = ZmqReplier("tcp://*:5555", async_handler, async_mode=True)

async def main():
    await replier.async_run()

asyncio.run(main())
```

#### 异步客户端

```python
import asyncio
from zmq_reqresp import ZmqRequester

async def client():
    req = ZmqRequester("tcp://127.0.0.1:5555", async_mode=True, timeout=5)
    response = await req.asend("Test message")
    print(response)

asyncio.run(client())
```

---

## 异常处理

| 场景 | 抛出异常 |
|------|----------|
| 在异步模式下调用同步 `send` 方法 | `Exception('ZMQ_Requester: in async mode, use asend instead')` |
| 在同步模式下调用异步方法 | `Exception('ZMQ_Requester: not in async mode, use send instead')` |
| 非异步模式下传入协程处理器 | `TypeError`（原代码有误，应为 `raise TypeError(...)`） |

> ❗ 原始代码中的 `raise('not in async mode...')` 存在语法错误，应改为：
```python
raise TypeError('not in async mode, handler can not be a coroutine')
```

---

## 注意事项

1. **资源管理**
   - `ZmqRequester.__del__` 中调用了 `_close()`，但在某些情况下 `__del__` 不一定被及时调用。建议显式管理生命周期。

2. **超时重连机制**
   - 当设置 `timeout > 0` 时，若接收超时，会自动关闭并重新连接。这可能导致短暂中断，适合容忍短暂失败的场景。

3. **ZmqReplier.stop() 中的 `join()` 错误**
   - 当前代码中 `self.join()` 未定义，因为 `Background` 对象未暴露或继承自 `Thread`。
   - 应确保 `Background` 类支持 `.join()` 方法，否则需移除或修复此行。

4. **异步模式下的 Poller 使用问题**
   - `asend_b` 中混合使用了 `poller.poll()`（同步）与 `await self.sock.recv_multipart()`（异步），这会导致阻塞风险。
   - 在异步模式下应避免使用 `Poller().poll()`，推荐使用 `asyncio.wait_for()` 包裹 `recv_multipart()`。

   ✅ 推荐改进方式：

   ```python
   try:
       r = await asyncio.wait_for(self.sock.recv_multipart(), timeout=self.timeout)
       return r[0]
   except asyncio.TimeoutError:
       self._close()
       self._connect()
       return None
   ```

5. **REP 套接字状态一致性**
   - 必须保证每次 `recv` 后都有对应的 `send`，否则套接字将进入非法状态。本模块通过结构化流程保障这一点。

6. **线程安全**
   - `ZmqRequester` 不是线程安全的，每个线程应使用独立实例。

---

## 版本建议改进

| 问题 | 建议修复 |
|------|---------|
| `raise('string')` 语法错误 | 改为 `raise Exception(...)` |
| `stop()` 调用未定义 `join()` | 移除或确保 `Background` 支持 `.join()` |
| 异步超时检测使用同步 Poller | 改用 `asyncio.wait_for()` |
| `rb =self.self.handler(b)` 拼写错误 | 应为 `rb = self.handler(b)` |

✅ 已发现拼写错误：

```python
rb =self.self.handler(b)  # 错误！
```

应修正为：

```python
rb = self.handler(b)
```

---

## 总结

`zmq_reqresp.py` 提供了一个简洁实用的 ZeroMQ 请求-响应通信封装，支持同步与异步双模式，在微服务、RPC 场景中有良好应用潜力。尽管存在少量 bug 和设计瑕疵，但整体架构清晰，易于扩展和维护。

> 建议结合 `contextlib` 或 `async context manager` 进一步增强资源管理能力。

--- 

📌 **作者**：未知  
📅 **最后更新**：2025年4月5日