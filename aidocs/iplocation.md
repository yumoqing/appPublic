# IP 地理位置查询工具技术文档

本项目提供一个基于多个公共 IP 定位 API 的 Python 工具，用于获取指定 IP 地址的地理位置信息（如国家、城市、经纬度等）。支持自动切换不同服务以提高成功率。

---

## 目录

- [简介](#简介)
- [依赖库](#依赖库)
- [核心功能](#核心功能)
- [函数说明](#函数说明)
  - [`get_outip()`](#get_outip)
  - [`ipip(ip=None)`](#ipipipnone)
  - [`ipapi_co(ip)`](#ipapi_coip)
  - [`ip_api_com(ip)`](#ip_api_comip)
  - [`iplocation(ip=None)`](#iplocationipnone)
  - [`get_ip_location(ip)`](#get_ip_locationip)
- [使用方式](#使用方式)
- [示例输出](#示例输出)
- [注意事项](#注意事项)

---

## 简介

该脚本通过调用多个第三方 IP 地理位置查询接口（如 `ip-api.com`、`ipapi.co`、`ipip.net` 和 `iplocate.io`），实现对任意 IP 地址的位置解析。当某个服务不可用或返回错误时，会自动尝试下一个服务，确保结果的可靠性。

主要用于：
- 获取本机公网 IP
- 查询任意 IP 的地理位置信息
- 多服务容错机制保障高可用性

---

## 依赖库

```txt
requests
beautifulsoup4 (未实际使用，可移除)
appPublic.http_client.Http_Client
appPublic.sockPackage.get_free_local_addr
```

> ⚠️ 注意：`appPublic` 是自定义模块，需确保其在系统路径中可用。

---

## 公共请求头

```python
public_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3100.0 Safari/537.36"
}
```

所有对外 HTTP 请求均携带此 User-Agent，模拟现代浏览器行为，避免被目标站点拒绝。

---

## 函数说明

### `get_outip()`

获取当前主机的公网 IPv4 地址。

#### 返回值
- `str`: 当前公网 IP 地址字符串（例如 `"8.8.8.8"`）

#### 实现原理
通过访问 `https://api.ipify.org` 获取外网出口 IP。

#### 示例
```python
print(get_outip())  # 输出: 123.45.67.89
```

---

### `ipip(ip=None)`

使用 [ipip.net](http://freeapi.ipip.net/) 免费 API 查询 IP 位置信息。

#### 参数
- `ip` (`str`, 可选): 要查询的 IP 地址；若为 `None`，则自动获取本机公网 IP。

#### 返回值
```json
{
  "country": "中国",
  "city": "北京"
}
```

#### 接口地址
```
http://freeapi.ipip.net/{ip}
```

> ⚠️ 返回数据为数组格式，脚本仅提取第 0 项（国家）和第 2 项（城市）。

---

### `ipapi_co(ip)`

使用 [ipapi.co](https://ipapi.co/) 提供的 JSON 接口查询 IP 信息。

#### 参数
- `ip` (`str`): 要查询的 IP 地址。

#### 返回值
标准化字段命名后的字典，包含：
```json
{
  "ip": "xxx.xxx.xxx.xxx",
  "country": "CN",
  "region": "Beijing",
  "city": "Beijing",
  "latitude": 39.9042,
  "longitude": 116.4074,
  "City": "Beijing",        // 兼容大写键名
  "lat": 39.9042,           // 别名
  "lon": 116.4074           // 别名
}
```

> ✅ 自动映射 `city → City`, `latitude → lat`, `longitude → lon`

---

### `ip_api_com(ip)`

使用 [ip-api.com](http://ip-api.com/json/) 查询 IP 地理信息。

#### 参数
- `ip` (`str`): 要查询的 IP 地址。

#### 返回值
原始响应基础上添加了兼容性字段：
```json
{
  "status": "success",
  "country": "China",
  "city": "Beijing",
  "City": "Beijing"   // 添加大写别名
}
```

---

### `iplocation(ip=None)`

使用 [iplocate.io](https://www.iplocate.io/) API 查询 IP 信息（需要 API Key）。

#### 参数
- `ip` (`str`, 可选): 查询 IP，若为空则使用公网 IP。

#### API Key
硬编码于代码中：
```python
apikey = 'c675f89c4a0e9315437a1a5edca9b92c'
```

> 🔐 **安全提示**：API Key 应配置为环境变量或配置文件管理，不建议明文写入代码。

#### 接口地址
```
https://www.iplocate.io/api/lookup/{ip}?apikey={apikey}
```

#### 返回值
JSON 格式的完整定位信息，包括国家、地区、城市、经纬度、时区等。

---

### `get_ip_location(ip)`

主入口函数：按优先级顺序尝试多个 IP 查询服务，返回第一个成功的结果。

#### 参数
- `ip` (`str`): 待查询的 IP 地址。

#### 执行流程
1. 按照以下顺序依次调用查询函数：
   - `ip_api_com`
   - `ipapi_co`
   - `ipip`
   - `iplocation`
2. 每个函数包裹在 `try-except` 中，失败则跳过。
3. 返回首个成功响应的数据。
4. 若全部失败，则返回 `None`。

#### 设计目的
提供**高可用、容错性强**的 IP 查询能力。

---

## 使用方式

### 命令行运行

```bash
python script.py [IP地址]
```

#### 示例

```bash
# 查询特定 IP
python script.py 8.8.8.8

# 查询本机公网 IP 位置
python script.py
```

> 💡 如果未传入参数，则默认查询本机公网 IP 的位置信息。

### 作为模块导入

```python
from your_module import get_ip_location

info = get_ip_location("8.8.8.8")
print(info)
```

---

## 示例输出

```json
{
  "ip": "8.8.8.8",
  "country": "United States",
  "city": "Mountain View",
  "region": "California",
  "lat": 37.4056,
  "lon": -122.0775,
  "timezone": "America/Los_Angeles"
}
```

具体字段取决于所使用的后端服务。

---

## 注意事项

1. **异常处理较粗略**
   - 所有异常均被捕获但无日志记录，不利于调试。
   - 建议改进为捕获特定异常并输出警告信息。

2. **API Key 明文暴露风险**
   - `iplocate.io` 的 `apikey` 写死在代码中，存在泄露风险。
   - 推荐方案：从环境变量读取
     ```python
     apikey = os.getenv('IPLOCATE_APIKEY', 'fallback-key')
     ```

3. **冗余导入**
   - `BeautifulSoup` 被导入但未使用，建议删除。
   - `os` 和 `sys` 仅用于基础操作，合理保留。

4. **HTTP 客户端复用问题**
   - 每次创建新的 `Http_Client()` 实例，可能影响性能。
   - 可考虑单例模式或连接池优化。

5. **服务降级策略**
   - 当前策略为“任一成功即返回”，适合大多数场景。
   - 如需更复杂逻辑（如多数投票、精度比较），可扩展。

6. **编码规范**
   - 缺少类型注解、函数 docstring。
   - 建议补充 PEP 257 文档字符串以增强可维护性。

---

## 未来优化建议

| 功能 | 描述 |
|------|------|
| 配置化 API 列表 | 将服务列表抽离至配置文件，便于动态调整顺序 |
| 缓存机制 | 对已查询过的 IP 进行内存缓存，减少重复请求 |
| 日志输出 | 加入 logging 模块支持，便于排查问题 |
| 异步支持 | 使用 `aiohttp` 改造为异步并发请求，提升效率 |
| 单元测试 | 编写测试用例验证各服务解析正确性 |

---

## 版权与许可

© 2025 作者保留所有权利。  
适用于内部工具或学习用途，生产环境请评估稳定性与安全性。

--- 

> 📝 文档版本：v1.0  
> 最后更新：2025年4月5日