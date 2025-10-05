# `UdpComm` 技术文档

```markdown
# UdpComm - UDP 通信模块技术文档

## 概述

`UdpComm` 是一个基于 Python 的异步 UDP 通信类，支持单播发送、广播、接收 JSON 或二进制数据，并通过后台线程处理 I/O 多路复用（`select`），适用于轻量级网络服务或设备发现等场景。

该模块封装了 UDP 套接字的基本操作，提供非阻塞接收与带缓冲的发送机制，同时支持自定义回调函数处理接收到的数据。

---

## 依赖说明

### 第三方/内部依赖
- `appPublic.sockPackage.get_free_local_addr`: 获取本机可用 IP 地址。
- `appPublic.background.Background`: 用于在后台运行任务的线程包装器。

> ⚠️ 注意：这两个模块属于项目私有库 `appPublic`，需确保其已安装并可导入。

### 内置模块
- `socket`: 提供底层网络通信功能。
- `select`: 实现 I/O 多路复用。
- `json`: 用于序列化和反序列化 JSON 数据。
- `time`: 控制循环延迟。
- `traceback.print_exc`: 打印异常堆栈信息。

---

## 常量

| 名称       | 值           | 说明 |
|------------|--------------|------|
| `BUFSIZE`  | `1024 * 64`  | 接收缓冲区大小，即每次最多接收 65536 字节 |

---

## 类定义：`UdpComm`

### 构造函数：`__init__(self, port, callback, timeout=0)`

初始化 UDP 通信实例。

#### 参数：
| 参数名     | 类型     | 必填 | 默认值 | 说明 |
|-----------|----------|------|--------|------|
| `port`    | int      | 是   | -      | 绑定的本地 UDP 端口号 |
| `callback`| function | 是   | -      | 回调函数，用于处理接收到的数据，签名应为 `callback(data, addr)` |
| `timeout` | float    | 否   | 0      | 超时时间（未启用） |

#### 初始化行为：
- 自动获取本机 IP 地址（用于后续广播计算）。
- 创建并绑定 UDP 套接字到指定端口 (`('', port)`)。
- 启动后台线程执行 `run()` 方法，持续监听消息。
- 初始化空发送缓冲队列 `buffer`。

> 📌 注：当前版本中 `setblocking` 和 `settimeout` 已被注释，实际为非阻塞模式配合 `select` 使用。

---

### 核心方法

#### `run(self)`
主循环逻辑，由后台线程执行。

##### 功能流程：
1. 使用 `select([sock], outs, [], 0.1)` 监听：
   - 输入事件：是否有数据可读。
   - 输出事件：是否可以发送数据（当缓冲区不为空时触发）。
2. 若有数据到达：
   - 调用 `recvfrom()` 读取数据。
   - 解析首字节标识符：
     - `'b'` → 视为原始 **bytes** 数据，直接传递给回调。
     - 其他 → 视为 UTF-8 编码的 JSON 字符串，尝试反序列化后传入回调。
   - 出错时打印异常及原始数据，但不停止运行（仅中断本次处理）。
3. 若可写且缓冲区有数据：
   - 从 `buffer` 中取出第一条待发消息并使用 `sendto()` 发送。
4. 循环结束条件：`self.run_flg == False`
5. 最终关闭套接字。

> ⏱️ 每次循环休眠 `0.1` 秒以降低 CPU 占用。

---

#### `stop(self)`
安全停止通信线程。

##### 行为：
- 设置标志位 `run_flg = False`，通知 `run()` 结束循环。
- 关闭 UDP 套接字。
- 等待后台线程退出（`join()`）。

> ✅ 推荐在程序退出前调用此方法释放资源。

---

#### `broadcast(self, data)`
向局域网广播消息（目标地址 `.255`）。

##### 参数：
| 参数名 | 类型 | 说明 |
|-------|------|------|
| `data` | any (serializable) or bytes | 要广播的数据 |

##### 处理逻辑：
- 若 `data` 非 `bytes` 类型，则将其 JSON 序列化并编码为 UTF-8。
- 构造广播地址（如本机 IP 为 `192.168.1.100`，则广播地址为 `192.168.1.255`）。
- 创建临时 UDP 客户端套接字，启用广播选项（`SO_BROADCAST=1`）。
- 发送数据到 `(broadcast_host, self.port)`。

> 🔊 广播不会经过 `send()` 缓冲区，是即时发送。

---

#### `send(self, data, addr)`
将数据加入发送缓冲区，异步发送至指定地址。

##### 参数：
| 参数名 | 类型         | 说明 |
|-------|--------------|------|
| `data` | str / dict / bytes | 待发送数据 |
| `addr` | tuple or list      | 目标地址 `(ip, port)` |

##### 数据封装规则：
- 若 `data` 不是 `bytes`：添加前缀 `'j'`，表示 JSON 数据。
- 若 `data` 是 `bytes`：添加前缀 `'b'`，表示二进制数据。

> 示例：
> - `send({"msg": "hello"}, ("192.168.1.2", 5000))` → 实际发送 `'j{"msg":"hello"}'`
> - `send(b'\x01\x02', ("192.168.1.2", 5000))` → 实际发送 `'b\x01\x02'`

> 🔄 数据会被追加到 `self.buffer`，由 `run()` 线程异步发送。

---

#### `sends(self, data, addrs)`
批量发送相同数据到多个地址。

##### 参数：
| 参数名  | 类型        | 说明 |
|--------|-------------|------|
| `data` | any / bytes | 要发送的数据 |
| `addrs`| list of tuple/list | 多个目标地址列表 |

##### 行为：
遍历 `addrs` 列表，对每个地址调用 `self.send(data, addr)`。

---

## 数据格式约定

| 首字节 | 含义       | 数据内容               |
|--------|------------|------------------------|
| `'b'`  | Binary     | 原始二进制数据（无编码） |
| `'j'`  | JSON       | UTF-8 编码的 JSON 字符串 |

接收端根据首字节判断如何解析后续数据。

---

## 回调函数规范

用户提供的 `callback` 函数必须接受两个参数：

```python
def callback(data, addr):
    # data: 解码后的对象（dict / list / bytes）
    # addr: 发送方地址 tuple(ip: str, port: int)
    pass
```

示例：
```python
def msg_handle(data, addr):
    print('addr:', addr, 'data=', data)
```

---

## 使用示例

### 作为服务器启动并监听

```bash
python udpcomm.py 50000
```

交互式输入格式：`目标端口:消息内容`

例如：
```
50001:{"cmd": "discover"}
```
→ 将 JSON 数据发送到 `localhost:50001`（IP 为空时自动替换为 `''`）

### 在代码中使用

```python
def on_message(data, addr):
    print(f"Received from {addr}: {data}")

# 启动监听
comm = UdpComm(port=50000, callback=on_message)

# 发送消息
comm.send({"hello": "world"}, ("192.168.1.50", 50000))

# 广播
comm.broadcast({"type": "service_announce"})

# 停止服务
comm.stop()
```

---

## 注意事项与限制

1. ❗ **线程安全**：`buffer` 未加锁，若多线程调用 `send()` 可能存在竞争风险。建议外部同步或改用线程安全队列。
2. 💤 **性能**：每轮 `sleep(0.1)` 可能影响实时性；可根据需要调整间隔。
3. 🧹 **错误处理**：JSON 解析失败仅打印日志，不会终止服务。
4. 🌐 **广播范围**：依赖子网掩码配置，`.255` 未必总是有效广播地址。
5. 🚫 **IPv6 不支持**：目前仅限 IPv4。

---

## TODO 改进建议

- [ ] 添加日志模块替代 `print`
- [ ] 使用 `queue.Queue` 替代 `list` 实现线程安全缓冲
- [ ] 支持 IPv6
- [ ] 增加单元测试
- [ ] 提供上下文管理器（`with` 支持）

---
```

> 文档版本：v1.0  
> 最后更新：2025-04-05