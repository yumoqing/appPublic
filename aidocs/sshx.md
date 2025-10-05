以下是为提供的 Python 代码编写的 **Markdown 格式技术文档**，涵盖了模块功能、类说明、方法描述及使用示例。

---

# SSH 连接管理模块技术文档

## 概述

本模块基于 `asyncssh` 实现了异步 SSH 客户端连接能力，支持通过跳板机（Jump Server）链式连接远程主机，并提供文件传输、命令执行和交互式 Shell 等高级功能。适用于批量运维操作、自动化部署与安全网络环境下的远程控制。

主要特性：
- 异步非阻塞 I/O，高并发处理多台服务器
- 支持密码或密钥认证
- 支持多级跳板机穿透
- 提供 SCP 文件上传下载接口
- 支持交互式命令执行（如 Bash）
- 封装简洁易用的高层 API

依赖库：
```bash
pip install asyncssh shlex
```

---

## 模块导入说明

```python
import os
import sys
import time
import shlex
from traceback import format_exc
from contextlib import asynccontextmanager
from functools import partial
from threading import Thread
from appPublic.myTE import tmpTml
from appPublic.log import debug, exception
import asyncio
import asyncssh
```

> 注意：`appPublic.*` 是项目自定义工具包，包含日志记录与模板引擎等功能。

---

## 核心类说明

### 1. `SSHServer`

表示一个可通过跳板机访问的目标 SSH 服务器。

#### 初始化参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `server` | dict | 目标服务器配置，格式见下表 |
| `jumpservers` | list[dict] | 跳板机列表（可选），每个元素结构同 `server` |

`server` 字典字段说明：

| 键名 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | str | 必填 | 主机地址（IP 或域名） |
| `username` | str | `'root'` | 登录用户名 |
| `port` | int | `22` | SSH 端口 |
| `password` | str | `None` | 登录密码（优先级低于密钥） |
| `client_keys` | list[str] | `[]` | 私钥路径列表（如 `['~/.ssh/id_rsa']`） |
| `passphrase` | str | `None` | 密钥加密口令 |
| `jumpservers` | list[dict] | `None` | 内嵌跳板机配置（若未传构造函数参数） |

#### 方法

##### `_connect_server(server: dict, refconn=None) -> asyncssh.SSHClientConnection`
内部方法，建立到指定服务器的连接。

- 若 `refconn` 存在，则通过已有连接隧道建立新连接（用于跳板穿透）
- 支持密钥或密码认证自动选择

##### `get_connector() -> Async Context Manager`
上下文管理器，返回目标主机连接对象，自动处理连接建立与释放。

**示例：**
```python
async with ssh_server.get_connector() as conn:
    result = await conn.run('ls -l')
    print(result.stdout)
```

> 自动关闭所有跳板机连接，异常时捕获并记录日志。

---

### 2. `SSHNode`

增强版 SSH 节点，封装完整生命周期管理与多种操作接口。

#### 初始化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | str | 必填 | 目标主机地址 |
| `username` | str | `'root'` | 用户名 |
| `port` | int | `22` | SSH 端口 |
| `password` | str | `None` | 登录密码 |
| `client_keys` | list[str] | `[]` | 客户端私钥路径 |
| `passphrase` | str | `None` | 私钥解密口令 |
| `jumpers` | list[dict] | `[]` | 跳板机列表 |

#### 属性

- `conn`: 当前节点主连接 (`asyncssh.SSHClientConnection`)
- `jumper_conns`: 所有跳板连接列表
- `batch_cmds`: 待执行命令队列（暂未完全实现）

#### 方法

| 方法 | 功能 |
|------|------|
| `info()` → dict | 返回当前节点信息快照 |
| `asjumper()` → list[dict] | 返回可用于其他节点跳板的配置列表 |
| `set_jumpers(jumpers)` | 动态设置跳板机 |
| `connect()` | 建立完整连接链（跳板 + 主机） |
| `close()` | 关闭所有连接资源 |
| `run(cmd, ...)` | 执行单条命令（自动连接/关闭） |
| `_cmd`, `_run`, `_process`, `_l2r`, `_r2l` | 内部操作封装 |

##### `run(cmd, input=None, stdin=None, stdout=None)`
执行远程命令，支持以下特殊语法：

- `l2r <local_path> <remote_path>`：本地 → 远程复制（SCP）
- `r2l <remote_path> <local_path>`：远程 → 本地复制（SCP）

否则调用 `conn.run()` 执行普通命令。

##### `_xcmd(cmd, xmsgs=[], ns={}, show_input=None, show_stdout=None)`
执行交互式命令，支持定时输入模拟。

- `xmsgs`: 输入消息列表，格式 `[ (delay_sec, template_string), ... ]`
- `ns`: 模板变量命名空间
- `show_input`, `show_stdout`: 回调函数，用于输出监控

> 示例：自动登录 CLI 工具、数据库等需要逐步输入的场景。

---

### 3. `SSHNodes`

批量管理多个 `SSHNode` 的容器类，支持并行执行。

#### 初始化参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `nodes` | list[str] | 主机名/IP 列表 |
| `username` | str | 统一用户名 |
| `port` | int | 统一端口 |
| `jumpers` | list[dict] | 共享跳板机配置 |

#### 方法

| 方法 | 功能 |
|------|------|
| `append_cmd(cmd, stdin, stdout)` | 添加待批处理命令 |
| `run(cmd, ...)` | 并发运行命令于所有节点 |
| `exe_batch()` | 执行预设批处理命令队列（**注意：当前存在 bug**） |

> 使用 `asyncio.gather(..., return_exceptions=True)` 避免单个失败中断整体流程。

#### 示例

```python
hosts = ['192.168.1.10', '192.168.1.11']
jump = {"host": "jumper.example.com", "username": "jumpuser", "port": 22}
cluster = SSHNodes(hosts, jumpers=[jump])

results = await cluster.run("uptime")
for r in results:
    if isinstance(r, Exception):
        print("Error:", r)
    else:
        print(r.stdout.strip())
```

---

### 4. `SSHBash`

实现交互式远程 Bash Shell 会话，支持实时输入输出转发。

#### 构造函数

```python
SSHBash(node: SSHNode, loop=None)
```

- `node`: 已配置的 `SSHNode` 实例
- `loop`: 可选事件循环（默认使用当前）

内部启动独立线程运行子事件循环，避免阻塞主线程。

#### 核心方法

##### `run(read_co, write_co)`
启动交互式 Bash 会话。

- `read_co`: 异步可调用对象，用于读取用户输入（例如从 `stdin`）
- `write_co`: 异步回调，用于写入输出内容（如打印到终端）

> 底层使用 `create_process('bash', term_type='xterm-256color')`

##### `feed_stdin(f)`
将输入数据推送到远程进程 stdin。

##### `exit()`
清理资源：关闭连接、停止子线程事件循环。

#### 使用示例

```python
async def read_input():
    return os.read(sys.stdin.fileno(), 65535)

async def write_output(data):
    sys.stdout.write(data.decode('utf-8'))
    sys.stdout.flush()

bash = SSHBash(my_ssh_node)
await bash.run(read_input, write_output)
```

---

### 5. `SshConnector`

轻量级连接包装器，提供更直观的操作接口。

> ⚠️ **Bug 提示**：`l2r` 方法中 `recurse=Tree` 应为 `recurse=True`

#### 方法

| 方法 | 功能 |
|------|------|
| `r2l(rf, lf)` | 下载文件：远程 → 本地 |
| `l2r(lf, rf)` | 上传文件：本地 → 远程 |
| `run_process(*args, **kw)` | 创建远程进程 |
| `run(cmdline, ...)` | 执行命令并返回结果 |

---

## 辅助函数与入口点

### `main()`
命令行交互入口，演示如何动态输入命令对多个主机批量执行。

```bash
python script.py "df -h" host1 host2 ...
```

> 当前版本进入无限循环等待用户输入。

### `test_sshbash()`
测试交互式 Bash 功能的示例函数。

---

## 已知问题与改进建议

| 问题 | 描述 | 建议修复 |
|------|------|---------|
| `SSHNodes.__init__` 拼写错误 | `usernmae` → `username` | 更正拼写 |
| `exe_batch()` 中 `return_excetion=True` | 拼写错误导致异常不被捕获 | 改为 `return_exceptions=True` |
| `exe_batch()` 在 `gather` 后仍有代码 | `return` 后不会执行后续行 | 移动 `for` 循环至 `gather` 之后 |
| `SshConnector.l2r` 中 `self.comm` | 应为 `self.conn` | 修正属性引用 |
| `show_result()` 中变量 `e` 未定义 | `print('Exception:', e)` 报错 | 改为 `print('Exception:', x)` |
| `recurse=Tree` | 应为布尔值 `True` | 修改为 `recurse=True` |

---

## 总结

该模块构建了一个灵活高效的异步 SSH 操作框架，特别适合在受限网络环境中通过跳板机批量管理服务器。结合 `asyncssh` 的强大功能，实现了文件传输、命令执行、交互式 Shell 等核心运维需求。

建议进一步完善单元测试、增加连接池、超时控制与重试机制以提升稳定性。

--- 

📌 **维护建议**：
- 添加类型注解（Type Hints）
- 补充 docstring 文档字符串
- 分离配置加载逻辑
- 增加连接健康检查机制

--- 

✅ **适用场景**：
- 自动化部署系统
- 多数据中心运维脚本
- DevOps 流水线中的远程操作环节
- 内网服务器集中管理平台

--- 

*文档版本：v1.0*  
*最后更新：2025年4月5日*