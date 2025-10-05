# RSA 加密工具类技术文档

```markdown
# RSA 加密与签名工具类（`RSA`）

基于 `python-rsa` 库封装的高级 RSA 加密、解密、签名与验证工具类，支持密钥生成、保存、读取、文本编解码、数据加解密及数字签名功能。

---

## 概述

本模块提供了一个简洁易用的 `RSA` 类，用于执行以下操作：

- 生成 RSA 公私钥对
- 保存和读取公私钥文件（PKCS#1 格式）
- 使用公钥加密、私钥解密（支持字符串和字节流）
- 数字签名（SHA-1 哈希）与验证
- 支持自定义字符编码（默认：`iso8859`）

> ⚠️ **注意**：当前签名使用的是 SHA-1 算法，安全性较低，仅适用于测试或兼容旧系统。生产环境建议升级为 SHA-256 或更高强度算法。

---

## 依赖库

- [`rsa`](https://pypi.org/project/rsa/)：纯 Python 实现的 RSA 加密库

安装方式：
```bash
pip install rsa
```

---

## 类定义

### `class RSA(keylength=4096, coding='iso8859')`

#### 参数说明：
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `keylength` | int | `4096` | RSA 密钥长度（单位：bit），常见值有 1024、2048、4096 |
| `coding`    | str | `'iso8859'` | 字符串编解码格式，用于文本与字节之间的转换 |

> 🔒 推荐密钥长度至少为 2048 bit；`iso8859` 编码不支持中文，如需处理中文请设为 `'utf-8'`

---

## 方法列表

---

### 初始化与配置

#### `__init__(self, keylength=4096, coding='iso8859')`
初始化 RSA 工具实例，设置默认密钥长度和字符编码。

---

### 密钥管理

#### `create_privatekey(self, keylength=4096) -> rsa.PrivateKey`
生成一个新的私钥。

- **参数**：
  - `keylength` (int): 密钥位数
- **返回**：`rsa.PrivateKey` 对象
- **示例**：
  ```python
  pri_key = rsa_instance.create_privatekey(2048)
  ```

#### `create_publickey(self, private_key: rsa.PrivateKey) -> rsa.PublicKey`
从私钥中提取对应的公钥。

- **参数**：
  - `private_key`: 私钥对象
- **返回**：`rsa.PublicKey` 对象

#### `write_privatekey(self, private_key, fname, password=None)`
将私钥写入文件（未加密存储，`password` 参数暂未实现加密）。

- **参数**：
  - `private_key`: 私钥对象
  - `fname` (str): 文件路径
  - `password` (str or None): （预留）未来可支持密码保护
- **文件格式**：PEM 编码的 PKCS#1 私钥（`.pem` 可读，但此处以二进制保存）

#### `write_publickey(self, public_key, fname)`
将公钥写入文件。

- **参数**：
  - `public_key`: 公钥对象
  - `fname` (str): 文件路径

#### `read_privatekey(self, fname, password=None) -> rsa.PrivateKey`
从文件读取私钥。

- **参数**：
  - `fname` (str): 文件路径
  - `password` (str or None): （预留）
- **返回**：私钥对象
- **异常处理**：文件不存在或格式错误会抛出异常

#### `read_publickey(self, fname) -> rsa.PublicKey`
从文件读取公钥。

- **参数**：
  - `fname` (str): 文件路径
- **返回**：公钥对象

#### `publickeyText(self, public_key) -> str`
将公钥序列化为文本字符串（Base64 编码 + PEM 结构，经指定编码转为 str）。

- **用途**：便于在网络上传输或嵌入 JSON 配置
- **返回**：编码后的字符串

#### `publickeyFromText(self, text) -> rsa.PublicKey`
从文本字符串恢复公钥对象。

- **参数**：
  - `text` (str): 由 `publickeyText()` 生成的字符串
- **返回**：公钥对象

---

### 加解密操作

#### `encode_bytes(self, public_key, bdata) -> bytes`
使用公钥加密原始字节数据。

- **参数**：
  - `public_key`: 公钥对象
  - `bdata` (bytes): 明文字节
- **返回**：密文字节

#### `decode_bytes(self, private_key, bdata) -> bytes`
使用私钥解密密文字节。

- **参数**：
  - `private_key`: 私钥对象
  - `bdata` (bytes): 密文字节
- **返回**：明文字节

#### `encode(self, public_key, text) -> str`
加密字符串（自动编码 → 加密 → 解码输出为字符串）。

- **参数**：
  - `public_key`: 公钥对象
  - `text` (str): 明文字符串
- **返回**：加密后的内容（字符串形式）
- **流程**：`text → encode(coding) → encrypt → decode(coding)`

> ❗ 输出是“可打印字符串”，但实际是乱码。传输时建议改用 Base64 编码避免损坏

#### `decode(self, private_key, cipher) -> str`
解密字符串（反向过程）。

- **参数**：
  - `private_key`: 私钥对象
  - `cipher` (str): 加密字符串
- **返回**：原始明文字符串

---

### 数字签名与验证

#### `sign_bdata(self, private_key, data_to_sign) -> bytes`
对字节数据进行 SHA-1 数字签名。

- **参数**：
  - `private_key`: 私钥对象
  - `data_to_sign` (bytes): 要签名的数据
- **返回**：签名字节

#### `sign(self, private_key, message) -> str`
对字符串消息进行签名，并返回字符串形式的签名。

- **参数**：
  - `private_key`: 私钥对象
  - `message` (str): 消息文本
- **返回**：签名字符串（经 `.coding` 解码）

#### `check_sign_bdata(self, public_key, bdata, sign) -> bool`
验证字节数据的签名是否有效。

- **参数**：
  - `public_key`: 公钥对象
  - `bdata` (bytes): 原始数据
  - `sign` (bytes): 签名字节
- **返回**：`True` if valid, else `False`
- **内部逻辑**：
  - 调用 `rsa.verify()` 返回哈希算法名（如 `'SHA-1'`）
  - 若匹配则返回 `True`，否则打印日志并返回 `False`
  - 异常捕获并返回 `False`

#### `check_sign(self, public_key, plain_text, signature) -> bool`
验证字符串消息及其签名。

- **参数**：
  - `public_key`: 公钥对象
  - `plain_text` (str): 原文
  - `signature` (str): 签名字符串
- **返回**：验证结果布尔值
- **流程**：`plain_text → bytes`, `signature → bytes` → 调用 `check_sign_bdata`

---

## 使用示例

```python
from your_module import RSA
import os

# 创建实例
r = RSA(keylength=2048, coding='utf-8')

# 生成密钥对
pri_key = r.create_privatekey()
pub_key = r.create_publickey(pri_key)

# 保存密钥到文件
r.write_privatekey(pri_key, 'private.pem')
r.write_publickey(pub_key, 'public.pem')

# 重新加载密钥
loaded_pri = r.read_privatekey('private.pem')
loaded_pub = r.read_publickey('public.pem')

# 加密解密测试
message = "Hello, RSA!"
cipher = r.encode(pub_key, message)
decrypted = r.decode(loaded_pri, cipher)
print("Decrypted:", decrypted)  # Should be same as original

# 签名与验证
signature = r.sign(pri_key, message)
is_valid = r.check_sign(pub_key, message, signature)
print("Signature valid?", is_valid)  # True
```

---

## 注意事项

1. **编码问题**：
   - 默认编码 `iso8859` 不支持中文。
   - 如需处理 Unicode 文本（如中文），建议初始化时设置 `coding='utf-8'`。

2. **安全性提醒**：
   - 当前签名采用 **SHA-1**，存在碰撞风险，不适合高安全场景。
   - 私钥文件目前以明文保存，无密码保护，请确保文件权限安全。

3. **性能限制**：
   - RSA 加密数据长度受限于密钥大小（例如 2048bit 最多加密 ~245 字节）。
   - 大量数据应结合 AES 使用（即混合加密体系）。

4. **异常处理**：
   - 所有读写文件操作均可能引发 `IOError` 或 `FileNotFoundError`。
   - 解密或验证失败会返回 `False` 并打印错误信息，建议在生产环境中优化日志级别。

---

## 主程序测试逻辑（`if __name__ == '__main__':`）

该部分包含一个持续增长字符串长度的自动化测试循环：

- 不断增加明文长度（从 100 字符开始，每次 +1）
- 测试加解密一致性
- 测试跨密钥签名与验证功能
- 输出包括：
  - 明文长度
  - 加密后密文长度
  - 是否能正确还原
  - 签名长度及验证结果

可用于压力测试或边界探测。

> 示例路径拼接可能需要调整以适应运行环境。

---

## 版本信息

- **作者**：Auto-generated Documentation
- **语言**：Python 3.x
- **库依赖**：`rsa>=4.0`
- **许可证**：MIT（假设）

---
```

> ✅ 提示：若用于正式项目，请补充单元测试、异常日志分级、Base64 编码接口以及更安全的签名算法扩展。