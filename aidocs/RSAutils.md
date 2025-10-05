# RSA 加密与签名工具库技术文档

本项目提供一个基于 Python 的 RSA 加密、解密、签名和验证功能的轻量级工具模块，使用 `PyCryptodome` 库实现核心密码学操作。支持密钥读取、生成、数据加密/解密以及数字签名/验证等功能。

---

## 📦 模块依赖

```python
import codecs
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Cipher import PKCS1_v1_5 as V1_5  # 注意：原代码拼写错误已修正
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA512, SHA384, SHA256, SHA, MD5
from Crypto import Random
from base64 import b64encode, b64decode
```

> ⚠️ **注意**：需要安装 `pycryptodome` 包：
>
> ```bash
> pip install pycryptodome
> ```

---

## 🔧 全局变量

| 变量名 | 类型   | 默认值       | 说明 |
|--------|--------|--------------|------|
| `hash` | string | `"SHA-256"`  | 当前使用的哈希算法名称，用于签名与验证（全局状态） |

> ❗ 警告：该变量为全局共享状态，在多线程或并发场景中可能导致不可预期行为，建议重构为参数传递方式。

---

## 📚 函数说明

### `readPublickey(fname) → RSA.RsaKey or None`

从文件读取公钥。

#### 参数：
- `fname` (str): 公钥文件路径（PEM 格式）

#### 返回值：
- 成功时返回 `RSA.RsaKey` 对象
- 失败时返回 `None`

#### 示例：
```python
pub_key = readPublickey('public.pem')
```

#### 文件格式要求：
```
-----BEGIN PUBLIC KEY-----
...Base64编码内容...
-----END PUBLIC KEY-----
```

---

### `readPrivatekey(fname, pwd) → RSA.RsaKey or None`

从文件读取带密码保护的私钥。

#### 参数：
- `fname` (str): 私钥文件路径（PEM 格式）
- `pwd` (str 或 bytes): 解密私钥的密码

#### 返回值：
- 成功时返回 `RSA.RsaKey` 对象
- 失败时返回 `None`

#### 示例：
```python
priv_key = readPrivatekey('private.pem', 'mysecretpassword')
```

#### 文件格式要求：
```
-----BEGIN ENCRYPTED PRIVATE KEY-----
...Base64编码内容...
-----END ENCRYPTED PRIVATE KEY-----
```

> ✅ 支持 AES 加密的 PEM 私钥（如 OpenSSL 生成）

---

### `newkeys(keysize) → (public_key, private_key)`

生成新的 RSA 密钥对。

#### 参数：
- `keysize` (int): 密钥长度（推荐 2048 或 4096）

#### 返回值：
- 元组 `(public_key: RsaKey, private_key: RsaKey)`

#### 示例：
```python
pub, priv = newkeys(2048)
```

> 💡 使用安全随机数生成器 (`Random.new().read`) 确保密钥安全性。

---

### `importKey(externKey) → RSA.RsaKey`

从字符串导入密钥（支持公钥或私钥）。

#### 参数：
- `externKey` (str 或 bytes): PEM 编码的密钥字符串

#### 返回值：
- `RSA.RsaKey` 对象

#### 示例：
```python
key_str = open("public.pem").read()
key = importKey(key_str)
```

---

### `getpublickey(priv_key) → RSA.RsaKey`

从私钥对象提取对应的公钥。

#### 参数：
- `priv_key` (RSA.RsaKey): 私钥对象

#### 返回值：
- 对应的公钥对象 (`RsaKey`)

#### 示例：
```python
pub_key = getpublickey(priv_key)
```

---

### `encrypt(message, pub_key) → bytes`

使用公钥加密消息（采用 PKCS#1 OAEP 填充，推荐用于新系统）。

#### 参数：
- `message` (bytes): 明文数据（必须是字节串）
- `pub_key` (RSA.RsaKey): 公钥对象

#### 返回值：
- 加密后的密文字节串 (`bytes`)

#### 示例：
```python
ciphertext = encrypt(b"Hello World", pub_key)
```

> 🔐 安全提示：OAEP 是抗适应性选择密文攻击的安全填充模式。

---

### `decrypt(ciphertext, priv_key) → bytes`

尝试使用私钥解密数据。优先使用 OAEP，失败后自动降级到 v1.5 填充。

#### 参数：
- `ciphertext` (bytes): 密文数据
- `priv_key` (RSA.RsaKey): 私钥对象

#### 返回值：
- 解密后的明文字节串 (`bytes`)
- 若两种模式均失败，则抛出异常并打印错误信息

#### 异常处理逻辑：
1. 首先尝试 `PKCS1_OAEP`
2. 失败则尝试 `PKCS1_v1_5`（兼容旧系统）
3. 打印异常详情（调试用）

> ⚠️ 自动降级可能带来安全隐患，请确保你知道为何使用 v1.5。

---

### `sign(message, priv_key, hashAlg="SHA-256") → bytes`

对消息进行数字签名（使用 PKCS#1 v1.5 签名方案）。

#### 参数：
- `message` (bytes): 待签名的消息
- `priv_key` (RSA.RsaKey): 私钥
- `hashAlg` (str): 哈希算法，可选值：
  - `"SHA-512"`
  - `"SHA-384"`
  - `"SHA-256"`（默认）
  - `"SHA-1"`
  - `"MD5"`

#### 返回值：
- 签名结果（原始字节流）

#### 内部逻辑：
根据 `hashAlg` 设置全局 `hash` 变量，并选择相应哈希函数计算摘要后签名。

#### 示例：
```python
signature = sign(b"important data", priv_key, "SHA-256")
```

> ❌ 不推荐使用 SHA-1 或 MD5，仅保留向后兼容。

---

### `verify(message, signature, pub_key) → bool`

验证数字签名的有效性。

#### 参数：
- `message` (bytes): 原始消息
- `signature` (bytes): 签名数据
- `pub_key` (RSA.RsaKey): 公钥对象

#### 返回值：
- `True`：签名有效
- `False`：签名无效或验证失败

#### 注意事项：
- 使用与 `sign()` 相同的全局 `hash` 变量决定哈希算法
- 必须保证签名时和验证时使用相同的哈希算法

#### 示例：
```python
is_valid = verify(b"important data", signature, pub_key)
if is_valid:
    print("✅ 签名验证通过")
else:
    print("❌ 签名无效")
```

---

## 🧪 主程序示例（测试用途）

```python
if __name__ == '__main__':
    cipher = """WaMlLEYnhBk+kTDyN/4OJmQf4ccNdk6USgtKpb7eHsYsotq4iyXi3N5hB1E/PqrPSmca1AMDLUcumwIrLeGLT9it3eTBQgl1YQAsmPxa6lF/rDOZoLbwD5sJ6ab/0/fuM4GbotqN5/d0MeuOSELoo8cFWw+7XpRxn9EMYnw5SzsjDQRWxXjZptoaGa/8pBBkDmgLqINif9EWV+8899xqTd0e9w1Gqb7wbt/elRNVBpgsSuSZb+dtBlvNUjuTms8BETSRai5vhXetK26Ms8hrayiy38n7wwEKE8fZ9iFzLtwa6xbhD5KudWbKJFFOZAfpzWttGMwWlISbGQigcW4+Bg=="""

    key = readPrivatekey('d:/dev/mecp/conf/RSA.private.key', 'ymq123')
    t = decrypt(b64decode(cipher), key)  # 注意：cipher 是 Base64 字符串，需先解码
    print('t=', t)
```

> 🔍 **Bug修复建议**：原文中的 `cipher` 是 Base64 字符串，但直接传给 `decrypt()` 会出错。应先用 `b64decode()` 转换为字节。

✅ 正确调用方式：
```python
t = decrypt(b64decode(cipher), key)
```

---

## 🛠️ 使用建议与注意事项

| 项目 | 建议 |
|------|------|
| 🔐 填充模式 | 推荐使用 `OAEP` 进行加密；`v1.5` 仅用于兼容老系统 |
| 📏 密钥长度 | 至少 2048 位，推荐 4096 以增强长期安全性 |
| 🧼 全局变量 `hash` | 存在并发风险，建议改为函数参数传递 |
| 🧑‍💻 错误处理 | `decrypt()` 中的 `print(e)` 应替换为日志记录 |
| 🔄 签名一致性 | `sign` 和 `verify` 必须使用相同哈希算法 |
| 🧩 Base64 编码 | 输入输出建议封装编解码层以便外部使用字符串传输 |

---

## 📎 示例：完整加解密流程

```python
# 生成密钥对
pub, priv = newkeys(2048)

# 加密
msg = b"Secret message"
ciphertext = encrypt(msg, pub)

# 解密
plaintext = decrypt(ciphertext, priv)
print(plaintext)  # b'Secret message'

# 签名 & 验证
sig = sign(msg, priv, "SHA-256")
valid = verify(msg, sig, pub)
print(valid)  # True
```

---

## 📚 参考资料

- [PyCryptodome 官方文档](https://pycryptodome.readthedocs.io/)
- RFC 3447 – PKCS #1 v2.1
- NIST FIPS 180-4 – 安全哈希标准

---

## 📝 版本信息

- 创建日期：2025年4月5日
- 作者：AI 助手
- 许可：MIT（假设）

--- 

> ✅ 提示：将此 `.py` 文件保存为 `rsa_utils.py`，可通过 `import rsa_utils` 在其他模块中复用。