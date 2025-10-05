# Socket 通信模块技术文档

本项目提供了一个基于 Python 的简单 TCP 客户端/服务器通信框架，支持多线程并发处理客户端连接，并封装了后台任务调用机制。适用于本地测试、轻量级网络服务开发等场景。

---

## 目录

- [依赖说明](#依赖说明)
- [核心功能概览](#核心功能概览)
- [工具函数](#工具函数)
- [后台任务类](#后台任务类)
- [异常定义](#异常定义)
- [SocketServer 类](#socketserver-类)
- [SocketClient 类](#socketclient-类)
- [主程序示例](#主程序示例)
- [使用建议与注意事项](#使用建议与注意事项)

---

## 依赖说明

```python
import os
import time
import threading
import sys
import socket
```

所需标准库模块：
- `socket`：用于实现 TCP 网络通信。
- `threading`：支持多线程并发处理多个客户端连接。
- `time`：用于延时控制和测试。
- 其他为通用系统操作支持。

---

## 核心功能概览

| 组件 | 功能 |
|------|------|
| `get_free_local_addr()` | 获取当前机器可用的 IP 地址（通过 DNS 请求探测） |
| `background` / `BackgroundCall()` | 异步执行函数的线程包装器 |
| `SocketServer` | 多线程 TCP 服务器，可接受并异步处理多个客户端连接 |
| `SocketClient` | TCP 客户端，用于连接服务器、发送和接收数据 |
| 自定义异常 | `SocketServerError`, `SocketClientError` 提供清晰错误分类 |

---

## 工具函数

### `get_free_local_addr()`

获取本机在联网状态下对外通信所使用的 IP 地址和临时端口。

#### 函数签名
```python
def get_free_local_addr():
```

#### 返回值
- `(ip: str, port: int)`：元组形式返回本机出口 IP 和操作系统分配的临时端口号。

#### 实现原理
通过创建一个 UDP 套接字连接到公共 DNS 服务器 `8.8.8.8:80`，不实际发送数据，仅用于确定本地绑定地址。

> ⚠️ 注意：此方法依赖外网可达性；若无网络或防火墙限制可能失败。

#### 示例
```python
ip, port = get_free_local_addr()
print(ip)  # 输出如 '192.168.1.100'
```

---

## 后台任务类

### `class background(threading.Thread)`

封装一个可在后台运行的函数调用。

#### 属性
| 属性名 | 类型 | 描述 |
|-------|------|------|
| `func` | `callable` | 要执行的目标函数 |
| `kw`   | `dict` | 关键字参数传递给目标函数 |

#### 方法
##### `__init__(self, func, kw)`
初始化线程对象。

- **参数**：
  - `func`: 可调用对象（函数）
  - `kw`: 字典形式的关键字参数 `{key: value}`

##### `run(self)`
重写 `Thread.run()`，自动调用 `self.func(**self.kw)`。

---

### `BackgroundCall(func, datas)`

便捷函数：启动一个后台线程执行指定函数。

#### 参数
- `func`: 待执行函数
- `datas`: 传入该函数的关键字参数字典

#### 行为
- 创建 `background` 实例
- 调用 `.start()` 启动线程
- 不阻塞主线程

#### 示例
```python
def echo(data):
    print("Received:", data)

BackgroundCall(echo, {'data': 'Hello'})
# 在后台打印 "Received: Hello"
```

---

## 异常定义

### `class SocketServerError(Exception)`
表示服务器端发生的严重错误，例如绑定地址失败、未就绪运行等。

### `class SocketClientError(Exception)`
表示客户端连接或通信过程中出现的问题，如无法连接、读写出错等。

> 使用自定义异常便于上层捕获特定错误类型进行处理。

---

## SocketServer 类

多线程 TCP 服务器，监听指定地址和端口，每个新连接由独立线程处理。

### 类定义
```python
class SocketServer(threading.Thread)
```

继承自 `threading.Thread`，以非守护模式运行。

---

### 构造函数 `__init__(host, port, max_connect=10, callee=None)`

#### 参数
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | `str` | — | 绑定主机地址，如 `'localhost'` 或 `'0.0.0.0'` |
| `port` | `int` | — | 绑定端口号 |
| `max_connect` | `int` | `10` | 最大挂起连接数（listen 队列长度） |
| `callee` | `callable` | `None` | 处理每个客户端连接的回调函数 |

#### 回调函数原型
```python
def handler(conn: socket.socket, addr: tuple):
    pass
```
其中：
- `conn`: 客户端连接套接字
- `addr`: 客户端地址 `(ip, port)`

#### 初始化行为
- 设置守护线程为 `False`
- 创建并尝试绑定监听套接字
- 若成功则 `ready = True`，否则记录日志但继续构造

---

### 方法

#### `setSocketServer()`
内部方法：创建并配置服务器套接字。

- 创建 TCP 套接字 (`AF_INET`, `SOCK_STREAM`)
- 绑定 `(host, port)`
- 开始监听（最大连接队列长度为 `max_c`）
- 成功后设置 `self.ready = True`

> 若失败会打印错误信息但不会抛出异常（构造阶段容错）

#### `run()`
线程入口函数，循环接受客户端连接。

- 检查是否 `ready`，否则抛出 `SocketServerError`
- 进入无限循环等待客户端接入
- 每次接受连接后，使用 `BackgroundCall` 将 `callee` 函数异步执行

> 单个连接处理完全解耦，不影响主服务循环

#### `stop()`
请求停止服务器运行。

- 设置标志位 `keep_running = 0`
- 下一次循环将退出 `run()` 函数
- ⚠️ 当前已建立的连接不会被主动关闭

#### `callee(self, conn, addr)`（默认回显处理）
内置默认处理函数：持续接收数据并原样返回（回显服务），直到连接断开。

> ❗ 存在一个拼写错误：`con.close()` 应为 `conn.close()`

##### 修正建议
```python
def callee(self, conn, addr):
    try:
        while True:
            d = conn.recv(1024)
            if not d:  # 接收到空数据表示连接关闭
                break
            conn.send(d)
    finally:
        conn.close()  # 正确关闭连接
```

---

## SocketClient 类

TCP 客户端封装，提供连接管理及基本 I/O 操作。

### 构造函数 `__init__(host, port)`
自动尝试连接指定服务器。

#### 参数
- `host`: 服务器地址
- `port`: 端口

#### 行为
- 创建 TCP 套接字
- 调用 `connect()` 方法连接服务器
- 成功则 `ready=True`，失败则抛出 `SocketClientError`

---

### 方法

#### `timeout(tim)`
设置套接字阻塞模式和超时时间。

- `tim == 0`: 非阻塞模式
- `tim > 0`: 阻塞模式 + 超时秒数

> 内部调用 `setblocking()` 和 `settimeout()`

#### `connect()`
重新建立与服务器的连接。

- 若失败打印错误信息并抛出 `SocketClientError`

#### `read(size)`
从服务器读取最多 `size` 字节数据。

- 成功返回字节串（`bytes`）
- 失败打印错误并抛出 `SocketClientError`

#### `write(data)`
向服务器发送数据。

- `data` 必须是字节串（`bytes`），若传入字符串需先编码
- 错误时抛出异常

#### `close()`
关闭连接，释放资源。

- 调用 `sock.close()`
- 设置 `ready = False`

---

## 主程序示例

```python
if __name__ == '__main__':
    s = SocketServer('localhost', 12232)
    s.start()
    time.sleep(5)  # 等待服务器启动

    while True:
        c = SocketClient('localhost', 12232)
        msg = 'msg1'
        print("send:", msg)
        c.write(msg.encode())  # 注意：必须 encode 成 bytes
        d = c.read(1024)
        print("get:", d.decode())  # 解码为字符串
        c.close()
        time.sleep(1)
```

> ✅ 改进建议：添加异常处理防止客户端崩溃中断循环

---

## 使用建议与注意事项

### ✅ 推荐实践
1. **确保数据编码一致性**
   ```python
   c.write(b'msg')           # 字节串
   c.write('msg'.encode())   # 字符串转字节
   ```
2. **捕获异常避免中断**
   ```python
   try:
       c = SocketClient(...)
   except SocketClientError:
       time.sleep(1)
       continue
   ```
3. **合理设置超时**
   ```python
   c.timeout(5)  # 5秒超时防卡死
   ```

### ⚠️ 已知问题
| 问题 | 描述 | 建议修复 |
|------|------|---------|
| `con.close()` 拼写错误 | 导致连接未正确关闭 | 改为 `conn.close()` |
| `callee` 默认函数无异常处理 | 可能导致线程异常退出 | 包裹 `try...finally` |
| 构造中静默忽略异常 | 难以调试绑定失败原因 | 抛出或记录详细日志 |
| `write()` 中错误提示写成了 `'recv error'` | 日志误导 | 改为 `'send error'` |

### 🔧 可扩展方向
- 添加 SSL/TLS 支持
- 支持 IPv6
- 增加连接池或心跳检测
- 提供异步 IO 版本（asyncio）

---

## 许可证

本代码为示例用途，遵循 [MIT License](https://opensource.org/licenses/MIT)（除非另有声明）。

--- 

> 文档版本：v1.0  
> 更新日期：2025年4月5日