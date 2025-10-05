# `AcrossNat` 技术文档

```markdown
# AcrossNat - 穿越 NAT 的端口映射与公网 IP 获取工具

`AcrossNat` 是一个用于在 NAT（网络地址转换）环境中获取公网 IP 地址、自动探测并配置端口映射的 Python 类。它支持多种协议和技术，包括 **NAT-PMP** 和 **UPnP IGD**，并在无法使用这些协议时回退到公共 API 查询公网 IP。

---

## 概述

该类主要用于 P2P 应用、远程访问服务等需要穿透家庭路由器进行端口暴露的场景。通过优先使用本地 NAT 协议（如 UPnP 或 NAT-PMP），避免手动配置端口转发，提升部署自动化能力。

---

## 依赖库

- `natpmp`: 实现 NAT-PMP 协议通信
- `upnpclient`: 发现和操作 UPnP 兼容的网关设备
- `requests`: 用于 HTTP 请求（获取公网 IP）
- `.background` (内部模块): 可能用于后台任务处理（未在代码中直接使用）

> 注意：需确保上述第三方库已安装：
>
> ```bash
> pip install natpmp upnpclient requests
> ```

---

## 类定义

```python
class AcrossNat(object)
```

封装了 NAT 穿透相关的功能，包括：

- 自动探测 NAT-PMP / UPnP 支持状态
- 获取外部公网 IP
- 动态映射内网端口到外网端口
- 查询/删除端口映射

---

## 初始化方法

### `__init__(self)`

初始化 `AcrossNat` 实例，并尝试自动检测 NAT-PMP 和 UPnP 是否可用。

#### 属性说明：

| 属性 | 类型 | 描述 |
|------|------|------|
| `external_ip` | str or None | 缓存的公网 IP 地址 |
| `upnp` | UPnP Service Object or None | UPnP WANConnectionDevice 服务对象 |
| `pmp_supported` | bool | 是否支持 NAT-PMP 协议 |
| `upnp_supported` | bool | 是否支持 UPnP 协议 |

#### 行为：

1. 调用 `init_pmp()` 尝试获取公网 IP（测试 NAT-PMP 支持）
2. 调用 `init_upnp()` 探测 UPnP 网关并绑定服务

---

## 核心方法

### `init_upnp(self)`

尝试发现局域网中的 UPnP 网关设备，并绑定第一个匹配的 WAN 连接服务。

#### 异常处理：

- 若发现失败或无可用设备，则设置 `self.upnp_supported = False`
- 打印异常信息（含 traceback）

#### 实现细节：

- 使用 `upnpclient.discover()` 发现设备
- 匹配服务名称包含 `'WAN'` 和 `'Conn'` 的服务（如 `WANIPConnection1`）

---

### `init_pmp(self)`

尝试通过 NAT-PMP 协议获取公网 IP 地址以判断是否支持。

#### 异常处理：

- 若设备不支持 NAT-PMP（返回 `NATPMPUnsupportedError`），则设 `self.pmp_supported = False`

---

### `get_external_ip(self) -> str or None`

获取当前设备的公网 IPv4 地址，按优先级尝试以下方式：

1. **NAT-PMP**（最快，本地协议）
2. **UPnP IGD GetExternalIPAddress**
3. 备用方案：HTTP 请求公共 IP 服务
   - `https://api.ipify.org`
   - `https://ipapi.co/ip/`

#### 返回值：

- 成功时返回字符串格式的 IP 地址（如 `"8.8.8.8"`）
- 所有方式均失败时返回 `None`

#### 示例：

```python
nat = AcrossNat()
ip = nat.get_external_ip()
print(ip)  # 输出: 123.45.67.89
```

---

### `upnp_check_external_port(eport, protocol='TCP') -> bool`

检查指定的外网端口是否已被映射。

#### 参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `eport` | int | —— | 外部端口号 |
| `protocol` | str | `'TCP'` | 协议类型，可选 `'TCP'` 或 `'UDP'` |

#### 返回值：

- `True`：端口已被映射
- `False`：未被映射或调用失败

#### 注意：

此方法仅适用于 UPnP 支持环境。

---

### `upnp_map_port(inner_port, protocol='TCP', from_port=40003, ip=None, desc='test') -> int or None`

使用 UPnP 映射一个内网端口到外网端口。

#### 参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `inner_port` | int | —— | 内部主机监听端口 |
| `protocol` | str | `'TCP'` | 协议类型（大小写不敏感） |
| `from_port` | int | `40003` | 起始外网端口 |
| `ip` | str or None | 当前主机 IP | 内部客户端 IP 地址（若为空由网关自动识别） |
| `desc` | str | `'test'` | 端口映射描述 |

#### 行为逻辑：

从 `from_port` 开始递增查找空闲外网端口（最大至 52332），直到成功添加映射。

#### 返回值：

- 成功：返回分配的外网端口号（int）
- 失败：返回 `None`

#### 示例：

```python
ext_port = nat.upnp_map_port(8080, protocol='tcp', desc='Web Server')
if ext_port:
    print(f"Port mapped: {ext_port} -> 8080")
```

---

### `is_port_mapped(external_port, protocol='TCP') -> bool`

查询某个外网端口是否已被映射。

#### 参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `external_port` | int | —— | 外部端口号 |
| `protocol` | str | `'TCP'` | 协议类型 |

#### 返回值：

- `True`：已映射
- `False`：未映射
- 若 UPnP 不支持，抛出异常：`Exception('not implemented')`

---

### `port_unmap(external_port, protocol='TCP')`

删除指定的端口映射条目。

#### 参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `external_port` | int | —— | 要解绑的外网端口 |
| `protocol` | str | `'TCP'` | 协议类型 |

#### 行为：

仅当 UPnP 支持时调用 `delete_port_mapping` 删除映射。

> ⚠️ 当前 `upnpclient` 库可能不提供 `delete_port_mapping` 方法，请确认版本兼容性。

否则抛出异常：`Exception('not implemented')`

---

### `pmp_map_port(inner_port, protocol='TCP', from_port=40003) -> int or None`

使用 NAT-PMP 协议映射端口。

#### 参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `inner_port` | int | —— | 内部端口 |
| `protocol` | str | `'TCP'` | 协议类型 |
| `from_port` | int | `40003` | 起始外网端口 |

#### 实现：

- TCP：调用 `pmp.map_tcp_port(...)`
- UDP：调用 `pmp.map_udp_port(...)`
- 永久映射（`lifetime=999999999`）

#### 返回值：

- 成功：返回公网端口号
- 失败：抛出异常（由 `natpmp` 抛出）

---

### `map_port(inner_port, protocol='tcp', from_port=40003, lan_ip=None, desc=None) -> int or None`

统一入口：自动选择最佳方式（NAT-PMP > UPnP）来映射端口。

#### 参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `inner_port` | int | —— | 内部端口 |
| `protocol` | str | `'tcp'` | 协议（不区分大小写） |
| `from_port` | int | `40003` | 起始外网端口 |
| `lan_ip` | str | None | 内部客户端 IP |
| `desc` | str | None | 映射描述 |

#### 优先级策略：

1. 若 `pmp_supported == True` → 使用 `pmp_map_port`
2. 否则使用 `upnp_map_port`

#### 返回值：

- 成功：返回外网端口号
- 失败：返回 `None`

---

## 使用示例

```python
from acrosnat import AcrossNat

# 创建实例
nat = AcrossNat()

# 获取公网 IP
ip = nat.get_external_ip()
print("Public IP:", ip)

# 映射本地 8000 端口
mapped_port = nat.map_port(8000, protocol='tcp', desc='MyApp')
if mapped_port:
    print(f"Successfully mapped external port {mapped_port} to 8000")
else:
    print("Failed to map port")

# 查询某端口是否已映射
if nat.is_port_mapped(mapped_port, 'tcp'):
    print("Port still mapped.")
```

---

## 错误处理与健壮性设计

- 所有关键操作都包裹在 `try-except` 中，防止因单个功能失效导致程序崩溃
- 对不可用的功能自动降级（如关闭 `pmp_supported` 标志）
- 提供多级 fallback：
  - NAT-PMP → UPnP → Public API（IP 获取）
  - UPnP 端口扫描避免冲突

---

## 已知限制与注意事项

1. **依赖网关支持**：
   - 需要路由器开启 UPnP 或 NAT-PMP 功能
   - 部分运营商级 NAT（CGNAT）环境下仍无法映射

2. **安全性提示**：
   - 自动端口映射存在安全风险，建议配合防火墙使用
   - `NewLeaseDuration=0` 表示永久有效，重启后可能保留

3. **upnpclient.delete_port_mapping**：
   - 原生 `upnpclient` 可能未实现此方法，需自行扩展或打补丁

4. **并发问题**：
   - 多线程同时调用 `map_port` 可能造成端口竞争，建议加锁控制

---

## 未来改进方向

- 添加日志系统替代 `print()`
- 支持异步非阻塞操作（结合 `Background` 模块）
- 增加对 IPv6 的支持
- 实现定期刷新和自动清理机制
- 提供更详细的错误码反馈

---

## 许可证

请根据项目实际情况填写许可证信息（如 MIT、Apache-2.0 等）。
```

---

> ✅ 提示：将此文档保存为 `README.md` 或集成进 Sphinx 文档系统以便团队协作维护。