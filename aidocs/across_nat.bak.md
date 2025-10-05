# `AcrossNat` 技术文档

```markdown
# AcrossNat - 穿透 NAT 的端口映射工具

`AcrossNat` 是一个用于在 NAT（网络地址转换）环境中自动获取公网 IP 并进行端口映射的 Python 类。它支持多种协议和技术，包括 **NAT-PMP**、**UPnP** 以及通过公共 API 获取公网 IP 地址。

该模块主要用于 P2P 应用、远程服务暴露或需要从外网访问内网服务的场景中，简化网络穿透配置流程。

---

## 模块依赖

```python
from natpmp import NATPMP as pmp
from aioupnp.upnp import UPnP
from requests import get
from .background import Background
```

- `natpmp`: 提供对 NAT-PMP 协议的支持。
- `aioupnp`: 异步 UPnP 发现与操作库。
- `requests`: 用于 HTTP 请求以获取公网 IP。
- `Background`: （未直接使用，可能为后续扩展预留）

> 注意：本类为异步设计，大量方法需在异步上下文中调用。

---

## 类定义

```python
class AcrossNat(object)
```

### 功能概述

`AcrossNat` 封装了以下功能：

1. 自动检测并初始化 NAT-PMP 或 UPnP 支持。
2. 获取设备的公网 IP 地址。
3. 在路由器上创建 TCP/UDP 端口映射。
4. 查询和删除现有端口映射。

优先级顺序：
- 首选：NAT-PMP
- 其次：UPnP
- 最后：外部 Web API 查询公网 IP

---

## 初始化与属性

### `__init__(self)`

初始化 `AcrossNat` 实例，并尝试探测 NAT-PMP 支持。

#### 属性说明

| 属性 | 类型 | 描述 |
|------|------|------|
| `external_ip` | `str or None` | 当前获取到的公网 IP 地址 |
| `upnp` | `UPnP or None` | UPnP 客户端实例（延迟加载） |
| `pmp_supported` | `bool` | 是否支持 NAT-PMP 协议 |
| `upnp_supported` | `bool` | 是否支持 UPnP 协议（默认 True，暂未实现动态检测） |

> ⚠️ 当前 `upnp_supported` 字段不会因实际探测失败而设为 `False`，建议未来增强错误处理。

---

## 核心方法

### `init_upnp(self)` - 异步

异步发现并初始化 UPnP 网关设备。

```python
await self.init_upnp()
```

- 若 `self.upnp` 已存在，则不重复初始化。
- 使用 `UPnP.discover()` 自动查找本地网络中的 UPnP 网关。

> ✅ 必须在事件循环中调用此协程。

---

### `init_pmp(self)`

尝试通过 NAT-PMP 获取公网 IP 来判断是否支持该协议。

```python
try:
    self.external_ip = pmp.get_public_address()
except pmp.NATPMPUnsupportedError:
    self.pmp_supported = False
```

- 成功 → 设置 `external_ip` 并保留 `pmp_supported = True`
- 失败 → 设置 `pmp_supported = False`

> ❗ 此方法是同步的，但 `get_public_address()` 可能阻塞，建议改为异步封装。

---

### `get_external_ip(self)` - 异步

获取当前公网 IP 地址，按优先级尝试以下方式：

1. **NAT-PMP**
2. **UPnP**
3. **外部 API (`api.ipify.org` 或 `ipapi.co/ip/`)**

```python
ip = await across_nat.get_external_ip()
```

#### 返回值

- `str`: 公网 IPv4 地址
- 若所有方式均失败，抛出最后一个异常

#### 示例响应

```text
"8.8.8.8"
```

---

### `upnp_map_port(...)` - 异步

使用 UPnP 在路由器上添加端口映射。

#### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `inner_port` | int | — | 内部主机监听端口 |
| `protocol` | str | `'TCP'` | 协议类型 `'TCP'` 或 `'UDP'` |
| `from_port` | int | `40003` | 起始外部端口号 |
| `ip` | str or None | `None` | 内部 IP 地址（若为 None，则使用 `lan_address`） |
| `desc` | str or None | `None` | 映射描述 |

#### 行为逻辑

1. 若尚未初始化 UPnP，则先调用 `init_upnp()`
2. 查询已有映射，避免重复
3. 扫描 `[from_port, 52333)` 区间寻找可用外部端口
4. 添加映射并返回分配的外部端口
5. 若无可用端口（>52333），返回 `None`

> 📌 默认最大端口限制为 `52333`，可调整。

#### 返回值

- `int`: 分配的外部端口号
- `None`: 无法映射（如端口耗尽）

---

### `is_port_mapped(external_port, protocol='TCP')` - 异步

检查某个外部端口是否已被映射。

> ⚠️ 当前逻辑有误！代码中判断 `len(x) == 0` 返回 `True`，语义相反。

#### 修正建议

```python
x = await self.upnp.get_specific_port_mapping(...)
return len(x) > 0  # 如果有映射记录，则已映射
```

否则会导致“没有映射 → 返回 True”这种反直觉行为。

#### 当前问题

- `len(x) == 0`: 没有找到映射 → 应返回 `False`（未映射）
- 但代码却返回 `True`，逻辑颠倒！

> 🔴 建议修复此 Bug。

---

### `port_unmap(external_port, protocol='TCP')` - 异步

删除指定的端口映射。

#### 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `external_port` | int | 要删除的外部端口号 |
| `protocol` | str | `'TCP'` 或 `'UDP'` |

#### 行为

- 删除对应的 UPnP 端口映射
- 若未启用 UPnP，则抛出异常 `'not implemented'`

> ✅ 实际已实现 UPnP 删除逻辑，但末尾仍抛出异常，应移除。

#### 建议修复

```python
await self.upnp.delete_port_mapping(external_port, protocol)
# 移除后面的 raise Exception('not implemented')
```

---

### `pmp_map_port(...)` - 同步

使用 NAT-PMP 创建永久端口映射（生命周期极长）。

#### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `inner_port` | int | — | 内部端口 |
| `protocol` | str | `'TCP'` | `'TCP'` 或 `'UDP'` |
| `from_port` | int | `40003` | 外部起始端口 |

> ⚠️ 注意：参数 `from_port` 在函数签名中声明但未使用！实际由系统自动选择。

#### 实现细节

- `lifetime=999999999`：几乎永久有效（约 31 年）
- 映射成功后返回 `public_port`

> ❌ 存在 Bug：UDP 分支前缺少 `elif`，导致无论协议如何都会执行 TCP 映射。

#### 修复建议

```python
if protocol.upper() == 'TCP':
    x = pmp.map_tcp_port(from_port, inner_port, lifetime=...)
else:
    x = pmp.map_udp_port(from_port, inner_port, lifetime=...)
```

否则 UDP 分支永远不会执行。

---

### `map_port(...)` - 异步

统一接口：自动选择 NAT-PMP 或 UPnP 进行端口映射。

#### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `inner_port` | int | — | 内部端口 |
| `protocol` | str | `'tcp'` | `'tcp'` 或 `'udp'`（不区分大小写） |
| `from_port` | int | `40003` | 起始外部端口 |
| `lan_ip` | str or None | `None` | 指定 LAN IP |
| `desc` | str or None | `None` | 映射描述 |

#### 优先级

1. 若 `pmp_supported` 为真 → 使用 `pmp_map_port`
2. 否则 → 使用 `upnp_map_port`

> ✅ 此方法作为高层抽象，推荐外部调用者使用。

---

## 使用示例

### 1. 获取公网 IP

```python
across = AcrossNat()
ip = await across.get_external_ip()
print("Public IP:", ip)
```

### 2. 映射端口

```python
external_port = await across.map_port(
    inner_port=8000,
    protocol='tcp',
    from_port=40003,
    desc='MyApp'
)
if external_port:
    print(f"Port mapped: {external_port} -> 8000")
else:
    print("Failed to map port")
```

### 3. 删除映射

```python
await across.port_unmap(external_port, 'TCP')
```

---

## 已知问题与改进建议

| 问题 | 描述 | 建议 |
|------|------|------|
| `is_port_mapped` 逻辑错误 | `len(x)==0` 返回 `True`，含义相反 | 修改为 `return len(x) > 0` |
| `port_unmap` 抛出异常 | 实现了但最后仍报错 | 移除 `raise Exception` |
| `pmp_map_port` 缺少 `elif` | UDP 分支无效 | 改为 `if...else` 结构 |
| `from_port` 未传入 PMP 调用 | 参数被忽略 | 应传递至 `map_tcp/udp_port` |
| `upnp_supported` 不会置为 False | 缺乏错误捕获机制 | 应在 `init_upnp` 中捕获异常设置标志 |
| `init_pmp` 为同步方法 | 可能阻塞事件循环 | 建议包装成异步或在线程中运行 |

---

## 总结

`AcrossNat` 提供了一个简洁、多协议兼容的 NAT 穿透解决方案，适用于需要动态开放端口的应用场景。尽管存在少量逻辑 Bug 和设计瑕疵，但整体结构清晰，易于集成。

✅ 推荐用于：
- P2P 网络通信
- 内网穿透工具
- DHT 节点部署
- 自托管服务暴露

🔧 建议修复上述 Bug 并增加日志输出以提升稳定性。

---
```