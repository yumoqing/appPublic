# `IpGetter` 与 `OutIP` 模块技术文档

---

## 概述

本模块提供了一个用于获取当前公网 IP 地址的 Python 工具类，支持从多个公开 IP 查询服务中获取 IP，并具备以下特性：

- 支持多源 IP 获取
- 自动统计请求耗时并按响应速度排序调用
- 内置 IP 格式校验
- 可扩展自定义解析器
- 容错处理（异常捕获、失败降级）

主要包含两个核心类：
- `IpGetter`：单个 IP 获取器，封装对一个 URL 的请求和解析逻辑。
- `OutIP`：管理多个 `IpGetter` 实例，智能选择最快可用的服务。

---

## 安装依赖

```bash
pip install requests
```

> 说明：该模块依赖 `requests` 库发送 HTTP 请求，需提前安装。

---

## 类与方法详解

### ✅ `class IpGetter(url: str, parser: Callable[[str], str])`

表示一个从指定 URL 获取公网 IP 的客户端。

#### 参数
| 参数 | 类型 | 说明 |
|------|------|------|
| `url` | `str` | 提供 IP 地址的公共 API 端点 URL |
| `parser` | `Callable[[str], str]` | 一个函数，用于从 HTTP 响应文本中提取原始 IP 字符串 |

#### 属性
| 属性名 | 类型 | 初始值 | 说明 |
|--------|------|--------|------|
| `cnt` | `int` | `0` | 成功请求次数（用于计算平均耗时） |
| `total_time` | `float` | `0` | 所有请求累计耗时（秒） |
| `avg_time` | `float` | `0` | 平均每次请求耗时（秒），失败后设为 10000 秒以降低优先级 |

#### 方法

##### `get() -> Optional[str]`
发起一次 IP 获取请求。

**流程：**
1. 记录开始时间
2. 使用 `requests.get()` 请求目标 URL
3. 调用 `parser` 函数从响应文本中提取 IP
4. 验证 IP 格式是否合法（通过正则）
5. 更新性能统计数据
6. 返回有效 IP 或 `None`

**返回值：**
- 成功时返回形如 `"123.45.67.89"` 的字符串
- 失败时打印错误信息并返回 `None`

> ⚠️ 若解析或格式校验失败，会将此实例的 `avg_time` 设为 `10000`，使其在后续调度中被排到末尾。

##### `check_ip(ip: str) -> Optional[str]`
使用正则表达式验证输入字符串是否为标准 IPv4 地址。

**正则模式：** `r'(\d+\.\d+\.\d+\.\d+)'`

**返回值：**
- 匹配成功：返回提取出的 IP 字符串
- 匹配失败：打印警告日志并返回 `None`

##### `get_average_time() -> float`
返回当前实例的历史平均请求耗时（单位：秒）。

##### `__str__() -> str`
返回调试字符串，格式如下：
```
self.url='...', self.avg_time=...
```

---

### ✅ `class OutIP()`

管理一组 `IpGetter` 实例，自动选择响应最快的可用服务来获取公网 IP。

#### 属性
| 属性名 | 类型 | 说明 |
|--------|------|------|
| `getters` | `List[IpGetter]` | 所有注册的 IP 获取器列表 |

#### 方法

##### `__init__()`
初始化 `OutIP` 实例，并调用 `set_known_getters()` 注册默认服务源。

##### `set_known_getters()`
预注册一组常用的公网 IP 查询服务，包括：

| URL | 解析方式 |
|------|----------|
| `http://ipinfo.io/ip` | 原样返回 |
| `https://api.ipify.org` | 原样返回 |
| `https://ident.me` | 原样返回 |
| `http://myip.dnsomatic.com` | 原样返回 |
| `https://checkip.amazonaws.com` | 去除首尾空白字符 |
| `http://checkip.dyndns.com` | 正则提取：`Address: X.X.X.X` |

> 💡 注释掉的服务示例：
> ```python
> # g = IpGetter('https://ipapi.co/ip/', lambda x: x)
> ```

##### `add_getter(getter: IpGetter)`
向管理器添加一个新的 `IpGetter` 实例。

##### `get() -> Optional[str]`
尝试从所有已注册的 `IpGetter` 中获取有效的公网 IP。

**策略：**
1. 将所有 `getters` 按 `get_average_time()` 升序排序（最快优先）
2. 依次调用每个 getter 的 `get()` 方法
3. 返回第一个成功的 IP
4. 若全部失败，返回 `None`

> 🔄 动态优化：随着运行时间增加，系统会学习哪些服务更快更稳定，优先使用它们。

---

## 使用示例

### 基本用法

```python
from outip import OutIP  # 假设保存为 outip.py
import time

oi = OutIP()

for i in range(10):
    ip = oi.get()
    print(f"Public IP: {ip}")
    time.sleep(1)
```

输出示例：
```
Public IP: 203.0.113.45
Public IP: 203.0.113.45
...
```

### 自定义 Getter 添加

```python
def custom_parser(text):
    match = re.search(r'current_ip["\']?: ?["\']?(\d+\.\d+\.\d+\.\d+)', text)
    return match.group(1) if match else None

custom_getter = IpGetter("https://myip.customservice.com", custom_parser)

oi = OutIP()
oi.add_getter(custom_getter)
ip = oi.get()
```

---

## 性能与容错机制

| 特性 | 描述 |
|------|------|
| **响应时间记录** | 每次成功请求都更新平均耗时，用于排序 |
| **失败惩罚机制** | 失败时设置 `avg_time = 10000`，避免频繁重试不可用服务 |
| **异常捕获** | 所有网络/解析异常被捕获，不影响主流程 |
| **服务降级** | 当首选服务失败时自动切换至备选服务 |

---

## 已知服务列表（内置）

| 服务名称 | URL | 是否启用 | 特点 |
|---------|------|----------|------|
| ipinfo.io | http://ipinfo.io/ip | ✅ 是 | 快速简洁 |
| ipify | https://api.ipify.org | ✅ 是 | 国际知名 |
| ident.me | https://ident.me | ✅ 是 | 支持多种格式 |
| dnsomatic | http://myip.dnsomatic.com | ✅ 是 | 老牌动态 DNS |
| Amazon AWS | https://checkip.amazonaws.com | ✅ 是 | AWS 官方服务 |
| DynDNS | http://checkip.dyndns.com | ✅ 是 | 返回 HTML，需正则提取 |

> 🔒 所有服务均为 HTTPS（除少数兼容 HTTP），建议生产环境优先使用加密连接。

---

## 注意事项

1. **线程安全**：当前实现非线程安全，多线程环境下请加锁或每个线程独立实例。
2. **频率限制**：部分服务可能对请求频率有限制，请合理控制调用间隔（如 `time.sleep(1)`）。
3. **代理影响**：若程序运行于 NAT 或代理之后，返回的是出口网关的公网 IP。
4. **IPv6 支持**：目前仅支持 IPv4；如需 IPv6，需修改正则及解析逻辑。

---

## TODO 扩展建议

- [ ] 支持异步 (`asyncio` + `aiohttp`)
- [ ] 加入缓存机制（避免短时间内重复请求）
- [ ] 支持配置文件加载自定义服务
- [ ] 提供 CLI 接口
- [ ] 增加单元测试覆盖率
- [ ] 支持 IPv6 格式校验

---

## 版权与许可

© 2025 开源工具模块  
可自由用于个人与商业项目，保留原作者注释即可。

--- 

📌 **提示**：将此代码保存为 `outip.py` 后可直接导入使用。