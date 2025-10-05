# Hugging Face SOCKS5 代理配置工具

该脚本用于为 `huggingface_hub` 库配置全局的 SOCKS5 代理，以便在受限网络环境下访问 Hugging Face 的模型和数据集资源。

---

## 📌 功能概述

- 使用 `requests.Session` 自定义 HTTP 后端会话。
- 通过 `huggingface_hub.configure_http_backend()` 设置自定义的请求会话工厂。
- 支持通过 SOCKS5 代理（使用 `socks5h://` 协议）转发所有对 Hugging Face Hub 的请求。
- 可灵活配置代理地址与端口。

> ✅ **推荐使用 `socks5h://` 而非 `socks5://`**：  
> `socks5h://` 会在 DNS 解析阶段也通过代理进行（防止 DNS 污染），而 `socks5://` 本地解析域名可能导致连接失败或泄露隐私。

---

## 🔧 安装依赖

确保已安装以下 Python 包：

```bash
pip install requests huggingface-hub[cli]
```

> 若需支持 SOCKS 代理，请额外安装：
> ```bash
> pip install requests[socks]
> ```

---

## 📄 模块说明

### 函数：`hf_socks5proxy(proxies)`

#### 参数

| 参数名   | 类型       | 默认值                                      | 说明 |
|--------|----------|------------------------------------------|------|
| `proxies` | `dict`   | `{ "http": "socks5h://127.0.0.1:1086", "https": "socks5h://127.0.0.1:1086" }` | 指定 HTTP 和 HTTPS 请求使用的代理协议及地址 |

> ⚠️ 注意：
> - 地址中的 `127.0.0.1:1086` 是常见本地代理监听端口（如 Clash、Shadowsocks 等客户端默认设置），请根据实际环境修改。
> - 必须同时设置 `http` 和 `https` 的代理项以确保兼容性。

#### 返回值

无返回值。此函数直接调用 `configure_http_backend()` 修改全局会话行为。

#### 内部逻辑

1. 定义一个 `backend_factory` 工厂函数，每次生成一个新的 `requests.Session` 实例。
2. 将传入的 `proxies` 配置应用到该 Session。
3. 使用 `huggingface_hub.configure_http_backend()` 注册此工厂函数为默认 HTTP 后端。
4. 所有后续由 `huggingface_hub` 发起的网络请求（如 `snapshot_download`, `hf_hub_download` 等）都将走指定的 SOCKS5 代理。

---

## 🧪 使用示例

### 基本调用（使用默认代理）

```python
from hf_proxy import hf_socks5proxy  # 假设保存为 hf_proxy.py

hf_socks5proxy()
```

### 自定义代理地址

```python
hf_socks5proxy({
    "http": "socks5h://192.168.1.100:1080",
    "https": "socks5h://192.168.1.100:1080"
})
```

### 验证是否生效（可选）

你可以结合日志输出或抓包工具确认流量是否经过代理。

---

## 📎 输出信息

运行时将打印如下调试信息：

```text
proxies={'http': 'socks5h://127.0.0.1:1086', 'https': 'socks5h://127.0.0.1:1086'}
socks5 proxy set proxies={'http': 'socks5h://127.0.0.1:1086', 'https': 'socks5h://127.0.0.1:1086'}
```

表示代理已成功设置。

---

## ⚠️ 注意事项

1. **必须安装 `PySocks` 支持**  
   如果未安装 `pysocks` 或 `requests[socks]`，程序会在使用代理时报错：
   ```
   Missing dependencies for SOCKS support.
   ```
   解决方法：
   ```bash
   pip install requests[socks]
   ```

2. **避免硬编码敏感信息**  
   不建议在代码中明文写死代理地址，生产环境中可通过环境变量注入：

   ```python
   import os
   proxy = os.getenv("SOCKS5_PROXY", "socks5h://127.0.0.1:1086")
   hf_socks5proxy({"http": proxy, "https": proxy})
   ```

3. **仅影响 `huggingface_hub` 的请求**  
   此配置不会改变其他库（如 `requests` 全局调用）的行为，仅作用于 `huggingface_hub` 内部发起的请求。

---

## 🧩 示例整合：下载远程模型

```python
from huggingface_hub import hf_hub_download
from hf_proxy import hf_socks5proxy

# 设置代理
hf_socks5proxy()

# 下载模型文件（自动走代理）
filepath = hf_hub_download(
    repo_id="bert-base-uncased",
    filename="config.json"
)
print(f"Downloaded to {filepath}")
```

---

## 📚 参考文档

- Hugging Face Hub SDK: [https://huggingface.co/docs/huggingface_hub](https://huggingface.co/docs/huggingface_hub)
- `configure_http_backend`: [https://huggingface.co/docs/huggingface_hub/en/reference/configure#huggingface_hub.configure_http_backend](https://huggingface.co/docs/huggingface_hub/en/reference/configure#huggingface_hub.configure_http_backend)

---

## 📎 版本历史

| 版本 | 描述 |
|------|------|
| v1.0 | 初始版本，支持基本 SOCKS5 代理注入 |

---

✅ 提示：将此功能封装为独立模块（如 `hf_proxy.py`），便于项目复用。