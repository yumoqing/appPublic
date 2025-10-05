# SSH 端口转发工具技术文档

## 概述

本项目实现了一个基于 `Paramiko` 的 SSH 端口转发（Port Forwarding）客户端，支持通过 SSH 隧道将本地端口映射到远程目标主机和端口。该工具可用于安全地访问内网服务或绕过防火墙限制。

主要功能：
- 建立 SSH 连接到跳板机（SSH Server）
- 在本地监听指定端口
- 将所有连接通过 SSH 隧道转发至目标主机（remote_host:remote_port）
- 支持动态配置、后台运行与手动启停控制

---

## 依赖库

| 库名 | 用途 |
|------|------|
| `paramiko` | 实现 SSH 客户端连接与通道管理 |
| `socket` | 网络通信、地址解析 |
| `select` | I/O 多路复用，用于双向数据转发 |
| `SocketServer` / `socketserver` | 构建 TCP 服务器以监听本地端口（兼容 Python 2/3） |
| `appPublic.background.Background` | 后台线程执行任务 |

> ⚠️ 注意：需确保已安装 `paramiko` 和 `appPublic` 包。

```bash
pip install paramiko
```

---

## 核心类说明

### 1. `ForwardServer` —— 多线程 TCP 服务器

继承自 `SocketServer.ThreadingTCPServer`，用于在本地监听端口并接受入站连接。

#### 特性
- `daemon_threads = True`：子线程随主线程退出而终止。
- `allow_reuse_address = True`：允许重用本地地址（避免端口占用问题）。
- `server_ready`：标志服务器是否已启动完成。
- `ready_callback`：服务器就绪时调用的回调函数。

#### 方法

| 方法 | 说明 |
|------|------|
| `service_actions()` | 重写父类方法，在首次服务启动后触发 `ready_callback` 回调 |
| `shutdown()` | 关闭服务器，并重置 `server_ready` 状态 |

---

### 2. `Handler` —— 请求处理器

继承自 `SocketServer.BaseRequestHandler`，处理每一个来自客户端的连接请求。

#### 属性（动态绑定）
- `ssh_transport`：SSH 传输通道（由外部注入）
- `chain_host`：目标主机地址（远程实际服务地址）
- `chain_port`：目标主机端口

#### 工作流程
1. 尝试通过 SSH 创建 `direct-tcpip` 类型的隧道通道
2. 若失败，打印错误日志并返回
3. 成功后进入循环：
   - 使用 `select.select()` 监听本地 socket 与 SSH channel 的可读事件
   - 双向转发数据（本地 ↔ SSH 隧道）
4. 任一端关闭连接时，清理资源并输出关闭信息

#### 日志输出示例
```
Connected! Tunnel open ('127.0.0.1', 50000) -> ('192.168.1.10', 22) -> ('10.0.0.5', 80)
Tunnel closed from ('127.0.0.1', 50000)
```

---

### 3. `SSHPortForward` —— 主控制器类

封装完整的 SSH 端口转发逻辑，提供简洁的接口用于启动/停止服务。

#### 构造函数参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `local_port` | int | 本地监听端口（如 8080） |
| `remote_host` | str | 目标主机域名或 IP（通过 SSH 跳转访问的目标） |
| `remote_port` | int | 目标主机端口 |
| `ssh_host` | str | SSH 服务器地址（跳板机） |
| `ssh_port` | int | SSH 服务端口（通常为 22） |
| `ssh_user` | str | SSH 登录用户名 |
| `ssh_password` | str | SSH 登录密码 |

#### 内部属性

| 属性 | 类型 | 描述 |
|------|------|------|
| `self.running` | bool | 当前服务是否正在运行 |
| `self._ready` | bool | 服务是否已准备就绪（可用于健康检查） |
| `self.ssh` | SSHClient | Paramiko SSH 客户端实例 |
| `self.transport` | Transport | SSH 传输层对象 |
| `self.forward_server` | ForwardServer | 本地监听服务器实例 |

#### 公共方法

##### `run()`
启动端口转发服务（异步非阻塞）。若已在运行，则忽略。

内部使用 `Background` 类在新线程中执行 `_run()`。

##### `_run()`
私有方法，运行于后台线程：

1. 连接 SSH 服务器（`connect_ssh_server()`）
2. 获取 SSH 传输通道
3. 动态创建 `MyForwardServer` 子类以设置回调
4. 动态创建 `SubHandler` 并注入 `chain_host`, `chain_port`, `ssh_transport`
5. 绑定到 `localhost:local_port` 并开始监听（`serve_forever()`）

##### `stop()`
停止当前运行的服务：

- 调用 `forward_server.shutdown()`
- 关闭 server socket
- 断开 SSH 连接（transport 和 client）

##### `service_ready()`
回调函数，当本地服务器成功启动后被调用，打印提示信息并将 `_ready` 设为 `True`。

---

### 4. 辅助函数

#### `connect_ssh_server(host, port, user, password)`
建立 SSH 连接并返回 `SSHClient` 实例。

- 自动添加未知主机密钥（`AutoAddPolicy`）
- 返回已连接的 SSH 客户端

#### `verbose(s)`
条件性打印调试信息，受全局变量 `g_verbose` 控制。

默认开启（`g_verbose = True`），可设为 `False` 关闭日志输出。

---

## 使用方式

### 命令行模式（主程序入口）

当直接运行脚本时，进入交互式控制台。

#### 启动命令格式

```bash
python ssh_forward.py <本地端口> <目标主机> <目标端口> <SSH主机> <SSH端口> <SSH用户> <SSH密码>
```

#### 示例

```bash
python ssh_forward.py 8888 example.internal 80 gateway.example.com 22 alice mypass123
```

此命令表示：
> 所有发往本机 `8888` 端口的流量，将通过 `gateway.example.com` 的 SSH 隧道，转发至 `example.internal:80`

#### 交互命令

程序启动后会显示菜单：

```
start) start server,
stop) stop server
quit) quit
```

输入对应指令即可操作服务状态。

---

## 工作原理图解

```
+-------------+       +------------------+       +--------------------+
|             |       |                  |       |                    |
|  Client     | ----> | Local Listener   | ----> | SSH Tunnel         | ----> Target Service
| (e.g. curl) |       | (SSHPortForward) |       | (via ssh_host)     |
|             |       |                  |       |                    |
+-------------+       +------------------+       +--------------------+
                          ↑
                      localhost:8888
```

1. 用户访问 `http://localhost:8888`
2. `SSHPortForward` 接收连接
3. 通过 SSH 隧道建立到 `remote_host:remote_port` 的 direct-tcpip 通道
4. 数据双向透明转发

---

## 错误处理与日志

- 所有异常均被捕获并输出详细信息（通过 `verbose()`）
- 常见错误包括：
  - SSH 认证失败
  - 目标主机无法解析（DNS）
  - SSH 服务器拒绝端口转发请求
  - 网络中断导致连接关闭

建议生产环境根据需要关闭 `g_verbose` 或重定向日志。

---

## 安全注意事项

1. **密码明文存储**：当前版本在内存中保存明文密码，不适用于高安全场景。建议扩展支持密钥认证（`.pem` 文件）。
2. **无加密本地通信**：本地监听仅限 `localhost`，防止外部访问敏感端口。
3. **自动信任主机密钥**：使用 `AutoAddPolicy()`，存在中间人攻击风险。生产环境应验证主机指纹。

---

## 扩展建议

| 功能 | 描述 |
|------|------|
| 支持私钥登录 | 添加 `pkey` 参数，替代密码认证 |
| 配置文件支持 | 使用 JSON/YAML 加载配置，避免命令行长参数 |
| REST API 控制 | 提供 HTTP 接口进行 start/stop 操作 |
| 日志模块替换 | 使用标准 `logging` 模块代替 `print` |
| 多隧道支持 | 管理多个并发转发规则 |
| 超时与心跳机制 | 防止长时间空闲断连 |

---

## 示例代码调用

```python
# 编程方式使用
tunnel = SSHPortForward(
    local_port=9000,
    remote_host="internal.db",
    remote_port=3306,
    ssh_host="jumpbox.company.com",
    ssh_port=22,
    ssh_user="dev",
    ssh_password="secret"
)

tunnel.run()  # 启动
# ... 使用一段时间 ...
tunnel.stop()  # 停止
```

---

## 版权与许可

- 作者：未知（请补充）
- 依赖开源库：Paramiko (LGPL), Python 标准库
- 使用遵循相应许可证要求

---

> ✅ 文档版本：v1.0  
> 📅 最后更新：2025-04-05