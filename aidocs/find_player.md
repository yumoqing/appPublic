# `BroadcastServer` 技术文档

本模块实现了一个基于 UDP 广播的发现服务，可用于局域网内设备或玩家的自动发现。主要包括一个广播服务器（`BroadcastServer`）和一个客户端发现函数（`find_players`）。

---

## 模块依赖

```python
from socket import *
import json
from appPublic.sockPackage import get_free_local_addr
from appPublic.background import Background
```

### 外部依赖说明：

- `socket`: 提供底层网络通信支持。
- `json`: 用于序列化/反序列化服务信息。
- `appPublic.sockPackage.get_free_local_addr`: 获取本地可用 IP 地址。
- `appPublic.background.Background`: 在后台线程中运行任务。

> ⚠️ 注意：`appPublic` 是自定义公共库，请确保其已安装并可导入。

---

## 常量定义

```python
BUFSIZE = 1024
```

- `BUFSIZE`: UDP 数据包最大接收缓冲区大小，单位为字节（1KB），适用于大多数局域网小数据传输场景。

---

## 类：`BroadcastServer`

一个 UDP 服务器，监听广播请求，并返回预设的服务信息（如主机名、端口等）给请求方。

### 构造函数：`__init__(self, port, info)`

#### 参数：
| 参数 | 类型 | 描述 |
|------|------|------|
| `port` | int | 服务器绑定的 UDP 端口号 |
| `info` | dict | 要广播的服务信息（例如：`{"name": "GameServer", "game_port": 8000}`） |

#### 功能：
1. 创建 UDP 套接字（IPv4, UDP）。
2. 设置套接字为阻塞模式（默认行为）。
3. 绑定到所有本地地址的指定端口 (`''` 表示 `0.0.0.0`)。
4. 启动后台线程运行 `run()` 方法。

#### 示例初始化：
```python
server_info = {
    "name": "Player1",
    "game_port": 6000,
    "status": "waiting"
}
bc_server = BroadcastServer(9999, server_info)
```

---

### 方法：`run()`

在后台持续运行，处理来自客户端的广播探测请求。

#### 流程：
1. 循环等待接收 UDP 数据包（最多 `BUFSIZE` 字节）。
2. 收到任意数据后，将 `self.info` 序列化为 JSON 并编码为 UTF-8 发送回请求者的地址。
3. 异常捕获打印日志但不中断服务。

> 📌 协议约定：任何发往该端口的数据都会触发响应 —— 即“有问必答”模型。

#### 响应格式（JSON）：
```json
{
  "name": "Player1",
  "game_port": 6000,
  "status": "waiting"
}
```

---

### 方法：`stop()`

安全停止服务器。

#### 功能：
- 设置运行标志 `run_flg = False`，终止 `run()` 循环。
- 关闭 UDP 套接字资源。
- 不主动等待线程结束（需业务层控制时序）。

#### 示例调用：
```python
bc_server.stop()
```

---

## 函数：`find_players(port)`

向局域网广播查询消息，寻找活跃的广播服务节点（如游戏主机）。

### 参数：
| 参数 | 类型 | 描述 |
|------|------|------|
| `port` | int | 目标广播服务器监听的端口号 |

### 返回值：
- `list[dict]`: 找到的设备信息列表，每个元素包含原始信息 + `'ip'` 字段。

```python
[
    {
        "name": "Player1",
        "game_port": 6000,
        "status": "waiting",
        "ip": "192.168.1.105"
    },
    ...
]
```

### 实现细节：

1. 使用 `get_free_local_addr()` 获取本机 IP，用于过滤自身响应。
2. 创建 UDP 客户端套接字并启用广播权限：
   ```python
   udpCliSock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
   ```
3. 绑定任意端口（`('', 0)`）。
4. 向 `255.255.255.255:{port}` 发送广播消息 `'findplayers'`。
5. 接收响应，超时时间为 5 秒。
6. 对每条有效响应：
   - 过滤非本地回环且非自身的 IP；
   - 解码 JSON 数据；
   - 添加来源 IP 到结果中；
7. 超时或异常时退出循环，返回收集结果。

> ✅ 支持跨子网？仅限局域网内支持广播的环境（通常不可跨路由）。

---

## 使用示例

### 启动广播服务（服务端）

```python
info = {"name": "MyGameHost", "game_port": 8888}
server = BroadcastServer(port=9999, info=info)

# ... 保持运行一段时间
# server.stop()  # 显式关闭
```

### 搜索局域网中的服务（客户端）

```python
players = find_players(9999)
for p in players:
    print(f"Found {p['name']} at {p['ip']}:{p['game_port']}")
```

输出示例：
```
Found MyGameHost at 192.168.1.105:8888
Found Player2 at 192.168.1.106:8889
```

---

## 注意事项与限制

| 项目 | 说明 |
|------|------|
| **协议** | UDP，不可靠传输，适合低延迟发现 |
| **广播地址** | 固定使用 `255.255.255.255`，适用于大多数局域网 |
| **安全性** | 无认证机制，仅适用于受信任内网 |
| **性能** | 单线程处理，适合轻量级发现场景 |
| **编码** | 默认使用 UTF-8 编码传输 JSON |
| **异常处理** | 已捕获异常防止崩溃，但建议上层监控 |

---

## 可能的改进方向

- ✅ 添加日志系统替代 `print`
- 🔧 支持多播替代广播以提高效率
- ⏱️ 可配置超时时间与重试次数
- 🛡️ 加入消息校验（如 magic header）
- 🔄 支持定期心跳广播（主动宣告）

---

## 版权与许可

© 2025 作者保留所有权利。  
仅供内部学习与开发使用，遵循项目整体开源协议（如有）。

--- 

📌 **提示**：部署前请测试网络环境是否允许广播通信。