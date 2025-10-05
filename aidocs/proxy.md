# SOCKS 代理设置工具技术文档

---

## 概述

该模块提供了一种简单的方式来为 Python 的全局网络请求设置和取消 SOCKS5 代理。通过替换 `socket.socket` 类，所有基于标准库 `socket` 的网络连接（包括 `requests` 等库）将自动通过指定的 SOCKS5 代理进行通信。

> ⚠️ 注意：此方法会影响全局 socket 行为，请谨慎使用，建议在完成代理请求后及时恢复原始设置。

---

## 依赖项

- Python 3.x
- `PySocks`：用于支持 SOCKS 代理
- `requests`：用于发起 HTTP 请求（示例用途）

### 安装依赖

```bash
pip install PySocks requests
```

---

## 函数说明

### `set_socks_proxy(host, port)`

启用 SOCKS5 代理，替换全局 `socket.socket` 实现。

#### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `host` | `str` | SOCKS5 代理服务器地址（如 `'127.0.0.1'`） |
| `port` | `int` | SOCKS5 代理服务端口（如 `1080`） |

#### 示例

```python
set_socks_proxy('127.0.0.1', 1080)
```

执行后，后续所有通过 `socket` 发起的连接（包括 `requests.get()` 等）都将通过该 SOCKS5 代理。

---

### `unset_proxy()`

恢复原始的 `socket.socket` 实现，关闭代理。

#### 说明

调用此函数后，所有网络连接将恢复为直连模式，不再经过代理。

#### 示例

```python
unset_proxy()
```

---

## 使用示例

```python
import requests
from your_module import set_socks_proxy, unset_proxy

# 设置 SOCKS5 代理
set_socks_proxy('127.0.0.1', 1080)

try:
    # 此请求将通过 SOCKS5 代理发送
    response = requests.get('https://httpbin.org/ip')
    print(response.json())
finally:
    # 务必恢复原始 socket 设置
    unset_proxy()
```

输出示例：
```json
{
  "origin": "1.2.3.4"
}
```
> 其中 IP 应为代理服务器的出口 IP。

---

## 注意事项

1. **线程安全**：由于修改了全局 `socket.socket`，在多线程环境下可能导致不可预期行为。不推荐在高并发或复杂应用中全局使用。
2. **异常处理**：建议在 `try...finally` 块中使用，确保 `unset_proxy()` 被调用。
3. **仅支持 SOCKS5**：当前实现固定使用 SOCKS5 协议，不支持认证或其他类型代理。
4. **影响范围广**：所有基于 `socket` 的库（如 `urllib`, `httplib`, `requests` 等）均会受影响。

---

## 扩展建议

- 支持更多代理类型（如 SOCKS4、HTTP）
- 添加用户名/密码认证支持
- 封装为上下文管理器以实现自动清理

```python
class SocksProxy:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __enter__(self):
        set_socks_proxy(self.host, self.port)

    def __exit__(self, *args):
        unset_proxy()

# 使用方式
with SocksProxy('127.0.0.1', 1080):
    requests.get('https://example.com')
```

---

## 版本兼容性

- Python: 3.6+
- PySocks: >=1.6.8

---

## 参考资料

- [PySocks GitHub](https://github.com/Anorov/PySocks)
- [requests - Python HTTP Library](https://docs.python-requests.org/)

--- 

📝 **维护建议**：在生产环境中，建议使用更精细的代理控制方式（如为 `requests.Session` 配置代理），避免修改全局 socket。