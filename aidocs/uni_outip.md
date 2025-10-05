# 外网 IP 获取工具技术文档

```markdown
# 外网 IP 获取工具（External IP Getter）

一个基于多协议尝试获取外网公网 IP 地址的 Python 工具，支持 NAT-PMP、UPnP 以及第三方网页抓取方式。通过多进程隔离输出流的方式安全地获取 IP 地址。

---

## 目录

- [功能概述](#功能概述)
- [依赖库](#依赖库)
- [核心模块与函数说明](#核心模块与函数说明)
  - [`pmp_get_external_ip()`](#pmp_get_external_ip)
  - [`upnp_get_external_ip()`](#upnp_get_external_ip)
  - [`ipgetter_get_external_ip()`](#ipgetter_get_external_ip)
  - [`get_external_ip()`](#get_external_ip)
  - [`outip(w)`](#outipw)
  - [`get_ip()`](#get_ip)
  - [`run()`](#run)
- [主程序入口](#主程序入口)
- [使用示例](#使用示例)
- [注意事项](#注意事项)
- [未来优化建议](#未来优化建议)

---

## 功能概述

本工具旨在可靠地获取当前设备所在的公网 IP 地址，采用多种协议逐级回退策略：

1. **NAT-PMP**：适用于支持该协议的路由器（如部分 Apple 设备）。
2. **UPnP IGD**：通用即插即用互联网网关设备协议，广泛用于家庭路由器。
3. **IPGetter 网页抓取**：当本地网络协议不可用时，通过访问公网服务获取 IP。

为避免跨进程通信中的阻塞和异常影响主流程，使用 `multiprocessing.Pipe` 和子进程隔离执行 IP 获取逻辑。

---

## 依赖库

| 库名 | 用途 |
|------|------|
| `natpmp` | 实现 NAT-PMP 协议以获取公网 IP |
| `upnpclient` | 发现并调用 UPnP IGD 服务 |
| `appPublic.ipgetter` | 第三方 IP 获取器（基于网页抓取） |
| `multiprocessing` | 多进程支持，用于隔离 IO 操作 |
| `os`, `time` | 系统操作与延时控制 |

> ⚠️ 安装命令：
```bash
pip install natpmp upnpclient app-public
```

---

## 核心模块与函数说明

### `pmp_get_external_ip()`

尝试通过 **NAT-PMP** 协议获取公网 IP。

#### 返回值
- 成功时返回字符串格式的公网 IP（如 `"203.0.113.45"`）
- 失败或异常时返回 `None`

#### 示例
```python
ip = pmp_get_external_ip()
if ip:
    print("NAT-PMP 获取成功:", ip)
```

---

### `upnp_get_external_ip()`

通过 **UPnP IGD**（Internet Gateway Device）协议从路由器获取公网 IP。

#### 流程说明
1. 调用 `upnpclient.discover()` 自动发现局域网内支持 UPnP 的网关设备。
2. 提取第一个设备，并查找包含 `'WAN'` 和 `'Conn'` 的服务名（通常是 WANIPConnection 或类似）。
3. 调用 `GetExternalIPAddress()` 方法获取外部 IP。
4. 解析响应中 `NewExternalIPAddress` 字段。

#### 返回值
- 成功时返回公网 IP 字符串
- 出错时打印错误信息并返回 `None`

> 📌 注意：若有多台 UPnP 设备，请注意选择正确的设备实例。

---

### `ipgetter_get_external_ip()`

使用第三方网页服务获取公网 IP，作为最后兜底方案。

#### 特点
- 使用 `appPublic.ipgetter.IPgetter` 类进行 HTTP 请求抓取。
- 内置重试机制，每 0.1 秒尝试一次直到成功。
- 忽略请求过程中的所有异常。

#### 返回值
- 成功获取后立即返回 IP 字符串
- 不会永久阻塞

---

### `get_external_ip()`

**主协调函数**：按优先级顺序尝试三种方法获取 IP。

#### 执行顺序
1. NAT-PMP
2. UPnP
3. Web 抓取（IPGetter）

一旦任一方法成功即返回结果，形成“短路”逻辑。

#### 返回值
- 公网 IP 字符串（推荐始终检查非空）
- 若全部失败，则返回 `None`

---

### `outip(w)`

在独立进程中运行的函数，将获取到的 IP 输出到指定写入端 `w`。

#### 参数
- `w`: 可写的文件描述符管道（来自 `Pipe()` 的写入端）

#### 原理
- 使用 `os.dup2(w.fileno(), 1)` 将标准输出重定向至管道
- 调用 `get_external_ip()` 并通过 `print(ip)` 输出
- 子进程结束后，父进程可通过读取管道获得结果

> ✅ 优点：避免复杂对象传递，利用文本流简化 IPC。

---

### `get_ip()`

主进程调用此函数来启动子进程并安全获取 IP。

#### 步骤
1. 创建匿名管道 `Pipe()`
2. 打开读取端为文件对象
3. 启动子进程执行 `outip(w)`
4. 读取子进程输出的第一行
5. 等待子进程结束
6. 返回去除了换行符的 IP 字符串

#### 返回值
- 成功：公网 IP 字符串（如 `"8.8.8.8"`）
- 失败：空字符串（需判断有效性）

---

### `run()`

持续运行的测试循环函数。

#### 行为
- 每 10 秒调用一次 `get_ip()`
- 若获取到 IP，则打印：`ip='203.0.113.45'`
- 使用 `time.sleep(10)` 控制频率

可用于长期监控公网 IP 变化。

---

## 主程序入口

```python
if __name__ == '__main__':
    run()
```

当脚本直接运行时，进入无限循环模式，每隔 10 秒输出当前公网 IP。

---

## 使用示例

### 单次获取 IP
```python
from your_module import get_ip

ip = get_ip()
print("Current Public IP:", ip)
```

### 集成进其他应用
可将 `get_external_ip()` 直接导入使用，无需多进程封装：

```python
from your_module import get_external_ip

public_ip = get_external_ip()
if public_ip:
    print(f"Public IP is {public_ip}")
else:
    print("Failed to retrieve public IP")
```

---

## 注意事项

1. **权限要求**
   - UPnP/NAT-PMP 需要设备处于同一局域网且路由器启用相应功能。
   - 某些防火墙可能阻止 SSDP（UPnP 发现协议）广播包。

2. **性能与延迟**
   - `ipgetter_get_external_ip()` 依赖网络请求，可能较慢。
   - 推荐仅作为备用手段。

3. **稳定性问题**
   - `upnpclient.discover()` 可能因网络波动返回空列表，导致索引错误。
   - 建议添加超时处理或重试逻辑。

4. **多进程开销**
   - `get_ip()` 每次创建新进程，不适合高频调用（如 >1次/秒）。

5. **输出重定向风险**
   - `os.dup2` 修改了子进程的标准输出，确保只在子进程中使用。

---

## 未来优化建议

| 改进项 | 描述 |
|--------|------|
| 添加超时机制 | 给每个 IP 获取方法设置最大等待时间 |
| 缓存最近 IP | 减少重复查询开销 |
| 支持更多协议 | 如 PCP（Port Control Protocol） |
| 异常日志记录 | 替代 `print()`，使用 `logging` 模块 |
| 配置化策略 | 允许用户配置启用哪些协议及顺序 |
| 异步支持 | 使用 `asyncio` + `aiohttp` 提升效率 |

---

## 许可证

请根据项目实际情况补充 LICENSE 信息。

> 示例：MIT License
```

--- 

✅ 文档完成。可保存为 `README.md` 或集成至 Sphinx/Docusaurus 文档系统。