# Topic Messaging System with ZeroMQ

这是一个基于 **ZeroMQ (ZMQ)** 的发布/订阅（Pub/Sub）消息系统，支持配置驱动的服务器、发布者和订阅者。该系统使用 `XPUB` 和 `XSUB` 套接字类型构建一个代理（proxy），实现多对多的消息广播机制。

---

## 📦 模块依赖

```python
import sys
import zmq
import time
from zmq import Context
from appPublic.jsonConfig import getConfig
```

- `zmq`: 使用 [pyzmq](https://pyzmq.readthedocs.io/) 实现高性能异步消息通信。
- `Context`: ZeroMQ 上下文对象，用于管理套接字资源。
- `getConfig()`: 来自 `appPublic.jsonConfig` 的工具函数，加载 JSON 格式的配置文件。

---

## 🔧 核心组件

### 1. `TopicServer` —— 主题消息代理服务器

#### 功能说明
`TopicServer` 是一个 ZeroMQ 代理服务，它通过 `zmq.XSUB` 接收来自多个发布者的主题消息，并通过 `zmq.XPUB` 将这些消息转发给所有匹配主题的订阅者。

> 它实现了经典的“反向代理”模式：前端接收发布者连接，后端向订阅者广播。

#### 初始化参数
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `address` | str | `'127.0.0.1'` | 绑定地址（可改为公网IP） |
| `pub_port` | str/int | `'5566'` | 发布者连接的端口（XSUB 端） |
| `sub_port` | str/int | `'5567'` | 订阅者连接的端口（XPUB 端） |

#### 构造函数行为
- 打印当前 ZeroMQ 库版本信息（libzmq 和 pyzmq）
- 创建全局上下文单例：`Context.instance()`
- 设置两个 TCP 地址：
  - `pub_port`: `tcp://<address>:<pub_port>` → 发布者连接此地址
  - `sub_port`: `tcp://<address>:<sub_port>` → 订阅者连接此地址
- 调用 `xpub_xsub_proxy()` 启动代理循环

#### 方法：`xpub_xsub_proxy()`
创建并启动 ZeroMQ 内置代理：

```python
zmq.proxy(frontend_pubs, backend_subs)
```

##### 套接字角色
| 套接字 | 类型 | 角色 | 绑定地址 |
|-------|------|------|---------|
| `frontend_pubs` | `XSUB` | 接收发布者消息 | `tcp://<address>:<pub_port>` |
| `backend_subs` | `XPUB` | 向订阅者广播消息 | `tcp://<address>:<sub_port>` |

> ✅ `bind()` 表示服务器监听连接；发布者与订阅者需调用 `connect()` 连接到对应端口。

##### 输出日志
```
Init proxy
Try: Proxy... CONNECT!
CONNECT successful!
```

> ⚠️ 注意：`zmq.proxy()` 是阻塞调用，程序会一直运行在此处直到中断。

---

### 2. `ConfiguredTopicServer` —— 配置驱动的代理服务器

继承自 `TopicServer`，从外部 JSON 配置文件读取参数。

#### 配置结构要求
```json
{
  "topicserver": {
    "address": "11.11.1.11",
    "pub_port": 1234,
    "sub_port": 1235
  }
}
```

> ⚠️ 错误拼写提示：原代码中 `"sub_server"` 应为 `"sub_port"`，否则将导致属性访问失败。

#### 异常处理
- 若配置不存在或缺少 `topicserver` 字段，则抛出未定义异常 `MissTopicServerConfig`（需提前定义）。

#### 示例用法
```python
server = ConfiguredTopicServer()
# 自动加载配置并启动代理
```

---

### 3. `TopicPublisher` —— 主题发布者客户端

允许向代理发送带主题的消息。

#### 初始化参数
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `topic` | str | `'en'` | 消息主题（如语言标识） |
| `address` | str | `'127.0.0.1'` | 代理的发布端地址 |
| `port` | str/int | `'5566'` | 代理的发布端口（对应 XSUB） |

#### 关键行为
- 将 `topic` 编码为 UTF-8 字节串（ZeroMQ 要求）
- 创建 `PUB` 套接字并连接到代理的 `pub_port`
- 添加 `time.sleep(0.5)`：防止连接未建立即发送消息（"slow joiner" 问题）

#### 方法：`send(message)`
发送一条多部分消息：`[topic_bytes, message_bytes]`

```python
publisher.send("Hello World")
# 实际发送: [b'en', b'Hello World']
```

> ✅ 支持任意字符串内容，自动编码为 UTF-8。

---

### 4. `ConfiguredTopicPublisher` —— 配置驱动的发布者

自动从配置文件读取代理地址和端口。

#### 用法示例
```python
pub = ConfiguredTopicPublisher(topic='news')
pub.send('Breaking news!')
```

> 使用配置中的 `address` 和 `pub_port`，无需硬编码。

---

### 5. `TopicSubscriber` —— 主题订阅者客户端

接收特定主题的消息。

#### 初始化参数
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `topic` | str/list | `''` | 订阅的主题（支持单个或列表） |
| `address` | str | `'127.0.0.1'` | 代理的订阅地址 |
| `port` | str/int | `'5567'` | 代理的订阅端口（对应 XPUB） |
| `callback` | callable | `None` | 收到消息时的回调函数 |

#### 订阅逻辑
- 若 `topic` 为字符串 → 订阅该主题
- 若 `topic` 为列表 → 循环订阅每个主题

```python
sub = TopicSubscriber(topic=['en', 'cn'])
```

> ZeroMQ SUB 套接字必须显式调用 `setsockopt(SUBSCRIBE, ...)` 才能接收消息。

#### 方法：`run()`
进入无限循环，持续接收消息：

```python
while True:
    msg_received = self.sub.recv_multipart()
    print("sub {}: {}".format(self.topic, msg_received))
    if self.callback:
        self.callback(msg_received)
```

> 输出格式示例：
```
sub en: [b'en', b'Hello']
```

---

### 6. `ConfiguredTopicSubscriber` —— 配置驱动的订阅者

类似其他配置类，自动加载代理连接参数。

#### 用法示例
```python
def on_msg(msg):
    print("Received:", msg)

sub = ConfiguredTopicSubscriber(topic='en', callback=on_msg)
sub.run()  # 开始监听
```

---

## 🌐 系统架构图（文本描述）

```
+-------------+         +---------------------+
| Publisher 1 |-------->|                     |
+-------------+         |   TopicServer       |
                        | (XPUB/XSUB Proxy)   |
+-------------+         |                     |---------> Subscriber A (topic=en)
| Publisher 2 |-------->|                     |---------> Subscriber B (topic=jp)
+-------------+         +---------------------+

                          ↑                ↑
                   pub_port (5566)   sub_port (5567)
```

- 所有发布者连接到 `pub_port`（XSUB）
- 所有订阅者连接到 `sub_port`（XPUB）
- 代理自动完成消息路由与过滤

---

## 🛠️ 使用示例

### 启动代理服务器（手动指定）
```python
server = TopicServer(address='0.0.0.0', pub_port=5566, sub_port=5567)
# 阻塞运行
```

### 或使用配置方式启动
```python
server = ConfiguredTopicServer()
```

### 发布消息
```python
pub = TopicPublisher(topic='en', address='localhost', port=5566)
pub.send("Hello English Users!")
```

### 订阅消息
```python
def handle_msg(msg_parts):
    topic, content = msg_parts
    print(f"Topic: {topic.decode()}, Msg: {content.decode()}")

sub = TopicSubscriber(topic='en', callback=handle_msg)
sub.run()
```

---

## ⚠️ 注意事项

1. **端口顺序不能错**：
   - 发布者连 `pub_port`（XSUB 输入）
   - 订阅者连 `sub_port`（XPUB 输出）

2. **延迟连接问题**：
   - `time.sleep(0.5)` 在发布者中是临时解决方案
   - 更优做法：使用同步机制（如 PULL/PUSH 协调）

3. **异常类缺失**：
   - `MissTopicServerConfig` 未在代码中定义，应补充：
     ```python
     class MissTopicServerConfig(Exception):
         pass
     ```

4. **编码一致性**：
   - 所有主题和消息均以 UTF-8 编码传输，确保跨平台兼容性。

5. **性能建议**：
   - `Context.instance()` 全局共享，避免频繁创建上下文
   - 多线程环境下注意套接字非线程安全

---

## 📁 配置文件样例 (`config.json`)

```json
{
  "topicserver": {
    "address": "127.0.0.1",
    "pub_port": 5566,
    "sub_port": 5567
  }
}
```

> 确保路径正确且 `getConfig()` 可读取。

---

## 📘 总结

| 组件 | 角色 | 套接字类型 | 连接方向 |
|------|------|------------|-----------|
| `TopicServer` | 消息代理 | XSUB + XPUB | bind |
| `TopicPublisher` | 消息生产者 | PUB | connect → pub_port |
| `TopicSubscriber` | 消息消费者 | SUB | connect → sub_port |

✅ 优点：
- 解耦发布者与订阅者
- 支持动态扩展
- 高吞吐低延迟
- 支持主题过滤

🔧 适用场景：
- 日志分发
- 实时通知系统
- 微服务间事件通信
- 多语言消息广播（如 en/jp/fr）

---

> 💡 提示：结合 Docker 部署 `TopicServer`，可实现跨主机消息分发。