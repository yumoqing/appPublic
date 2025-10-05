# RSA 密钥管理与签名验证工具技术文档

本项目提供一个基于 `cryptography` 库的轻量级 RSA 加密、解密、签名与验证功能封装，支持多种密钥格式（PEM、PKCS#1、PKCS#8、OpenSSH）的加载与写入。适用于需要安全地处理 RSA 公私钥及数字签名的应用场景。

---

## 📦 依赖库

```bash
pip install cryptography
```

> **注意**：`cryptography` 是一个使用 CFFI 绑定 OpenSSL 的密码学库，需确保系统中已安装必要的编译工具或预编译包。

---

## 🧩 模块功能概览

| 功能 | 描述 |
|------|------|
| `_load_private_key` | 从文件加载私钥（支持 PEM 和 OpenSSH 格式） |
| `_load_public_key` | 从文件加载公钥（支持 PEM 和 OpenSSH 格式） |
| `_write_private_key` | 将私钥写入文件（支持 PKCS#1, PKCS#8, OpenSSH 格式） |
| `_write_public_key` | 将公钥写入文件（支持 PEM, OpenSSH 格式） |
| `_sign` / `_verify` | 使用私钥签名和公钥验证数据（SHA256 + PKCS1v15） |
| `RSAer` 类 | 面向对象接口，集成密钥生成、读写、签名/验证等功能 |

---

## 🔐 私钥操作

### `_load_private_key(filepath: str, password: bytes = None) → RSAPrivateKey`

从指定路径加载私钥文件，自动识别格式并返回对应的 `RSAPrivateKey` 对象。

#### 参数：
- `filepath` (str): 私钥文件路径。
- `password` (bytes, optional): 解密加密私钥所需的口令（字节类型），若未加密可省略。

#### 支持格式：
| 开头标识 | 格式说明 |
|--------|---------|
| `-----BEGIN OPENSSH PRIVATE KEY-----` | OpenSSH 私钥格式 |
| `-----BEGIN RSA PRIVATE KEY-----` 或 `-----BEGIN PRIVATE KEY-----` | PEM 编码的私钥（PKCS#1 或 PKCS#8） |

#### 返回值：
- `RSAPrivateKey`: 成功时返回私钥对象。

#### 异常：
- `ValueError`: 不支持的私钥格式。
- `TypeError`: 密码错误或格式损坏。

#### 示例：
```python
private_key = _load_private_key("id_rsa", password=b"mypass")
```

---

### `_write_private_key(key, filepath, fmt="pkcs8", password: bytes = None)`

将私钥对象写入文件，支持加密保存。

#### 参数：
- `key` (`RSAPrivateKey`): 要写入的私钥对象。
- `filepath` (str): 输出文件路径。
- `fmt` (str): 输出格式，可选 `"pkcs8"`（默认）、`"pkcs1"`、`"openssh"`。
- `password` (bytes, optional): 若提供，则使用最佳可用算法加密私钥。

#### 支持格式：
| `fmt` 值 | 格式描述 |
|--------|----------|
| `pkcs8` | PEM 编码的 PKCS#8 格式（推荐） |
| `pkcs1` | PEM 编码的传统 RSA 私钥（仅限 RSA） |
| `openssh` | OpenSSH 原生私钥格式（兼容 OpenSSH 工具链） |

#### 注意事项：
- 当 `password` 不为 `None` 时，私钥将被加密存储。
- 所有输出均为二进制模式写入。

#### 示例：
```python
_write_private_key(private_key, "private_encrypted.pem", fmt="pkcs8", password=b"secret123")
```

---

## 🔍 公钥操作

### `_load_public_key(filepath: str) → RSAPublicKey`

从文件加载公钥，自动识别格式。

#### 参数：
- `filepath` (str): 公钥文件路径。

#### 支持格式：
| 文件内容开头 | 格式 |
|-------------|------|
| `ssh-rsa`, `ssh-ed25519` 等 | OpenSSH 公钥格式 |
| `-----BEGIN PUBLIC KEY-----` | PEM 编码的标准公钥（SubjectPublicKeyInfo） |

#### 返回值：
- `RSAPublicKey`: 成功时返回公钥对象。

#### 异常：
- `ValueError`: 不支持的公钥格式。

#### 示例：
```python
public_key = _load_public_key("id_rsa.pub")
```

---

### `_write_public_key(public_key, filepath, fmt="pem")`

将公钥对象写入文件。

#### 参数：
- `public_key` (`RSAPublicKey`): 公钥对象。
- `filepath` (str): 输出文件路径。
- `fmt` (str): 输出格式，支持 `"pem"`（默认）或 `"openssh"`。

#### 支持格式：
| `fmt` | 输出格式 |
|-------|---------|
| `pem` | PEM 编码的 X.509 公钥（标准格式） |
| `openssh` | OpenSSH 风格的单行公钥（如用于 `~/.ssh/authorized_keys`） |

#### 示例：
```python
_write_public_key(public_key, "public.pem", fmt="pem")
_write_public_key(public_key, "id_rsa_openssh.pub", fmt="openssh")
```

---

## ✍️ 数字签名与验证

### `_sign(prikey, data: bytes) → bytes`

使用私钥对数据进行 SHA256 + PKCS1v15 签名。

#### 参数：
- `prikey` (`RSAPrivateKey`): 有效的 RSA 私钥。
- `data` (bytes): 待签名的原始数据。

#### 返回值：
- `bytes`: 签名结果（二进制）。

#### 算法细节：
- 哈希算法：`SHA-256`
- 填充方式：`PKCS1v15`

> ⚠️ 注：也可替换为更现代的 `PSS` 填充以增强安全性。

#### 示例：
```python
signature = _sign(private_key, b"Hello World")
```

---

### `_verify(pubkey, data: bytes, signature: bytes) → bool`

验证数据签名是否有效。

#### 参数：
- `pubkey` (`RSAPublicKey`): 对应的公钥。
- `data` (bytes): 原始数据。
- `signature` (bytes): 签名值。

#### 返回值：
- `True`: 验证成功。
- `False`: 验证失败（包括异常捕获）。

#### 内部机制：
- 使用与 `_sign` 相同的参数（`PKCS1v15`, `SHA256`）进行校验。
- 捕获 `InvalidSignature` 异常并返回 `False`。

#### 示例：
```python
is_valid = _verify(public_key, b"Hello World", signature)
print(is_valid)  # True or False
```

---

## 🧱 RSAer 类：高级封装接口

`RSAer` 提供面向对象的方式统一管理密钥与操作。

### 初始化
```python
rsa_tool = RSAer()
```

属性初始化为空：
- `self.prikey = None`
- `self.pubkey = None`

---

### `.create_key(keylen=2048)`

生成新的 RSA 密钥对。

#### 参数：
- `keylen` (int): 密钥长度，默认 `2048`，建议至少 2048 位。

#### 生成规则：
- 公共指数固定为 `65537`（Fermat Prime，行业标准）
- 使用安全随机源生成大素数

#### 示例：
```python
rsa_tool.create_key(2048)
```

---

### `.write_private_key(filepath, fmt="pkcs8", password=None)`

导出私钥到文件。

#### 参数：
- `filepath`: 输出路径
- `fmt`: 格式（`pkcs8`, `pkcs1`, `openssh`）
- `password`: 可选加密口令（bytes）

> ❗ 抛出异常：若 `self.prikey` 为 `None`

#### 示例：
```python
rsa_tool.write_private_key("mykey.pem", fmt="pkcs8", password=b"pass123")
```

---

### `.write_public_key(filepath, fmt="pem")`

导出公钥到文件。

#### 参数：
- `filepath`: 输出路径
- `fmt`: `pem` 或 `openssh`

> ⚠️ 自动从私钥推导公钥（如果尚未设置）

#### 示例：
```python
rsa_tool.write_public_key("mykey.pub", fmt="openssh")
```

---

### `.load_private_key(filepath, password=None)`

加载已有私钥。

#### 示例：
```python
rsa_tool.load_private_key("private.pem", password=None)
```

---

### `.load_public_key(filepath)`

加载已有公钥。

#### 示例：
```python
rsa_tool.load_public_key("public.pem")
```

---

### `.sign(data: bytes) → bytes`

使用当前私钥签名数据。

#### 示例：
```python
sig = rsa_tool.sign(b"Important message")
```

---

### `.verify(data: bytes, signature: bytes) → bool`

使用当前公钥验证签名。

#### 示例：
```python
valid = rsa_tool.verify(b"Important message", sig)
assert valid == True
```

---

### ❌ 待实现方法
以下两个方法在代码中声明但未实现：

```python
def encode(self, data):
def decode(self, data):
```

> 后续可根据需求补充 RSA 加解密功能（通常用于小数据块加密，如密钥传输）。  
> 推荐使用 `padding.OAEP` 或 `PKCS1v15` 进行加密填充。

---

## 🧪 示例用法（主程序）

```python
if __name__ == '__main__':
    # 示例：加载私钥和公钥
    private_key = _load_private_key("path/to/private_key.pem", password=None)
    public_key = _load_public_key("path/to/public_key.pub")

    print("私钥类型:", type(private_key))
    print("公钥类型:", type(public_key))

    # 写出不同格式的私钥
    _write_private_key(private_key, "private_pkcs8.pem", fmt="pkcs8")
    _write_private_key(private_key, "private_pkcs1.pem", fmt="pkcs1")
    _write_private_key(private_key, "private_openssh", fmt="openssh")

    # 写出不同格式的公钥
    _write_public_key(public_key, "public.pem", fmt="pem")
    _write_public_key(public_key, "id_rsa.pub", fmt="openssh")

    # 签名与验证
    data = b"Secure message"
    signature = _sign(private_key, data)
    is_valid = _verify(public_key, data, signature)
    print("Signature valid?", is_valid)
```

---

## ✅ 安全建议

1. **密钥保护**：
   - 私钥应始终加密存储（使用强密码）。
   - 权限设为 `600`（Linux/macOS）防止他人读取。

2. **签名算法选择**：
   - 推荐使用 `PSS` 填充替代 `PKCS1v15` 以获得更强的安全性。
   - 示例修改：
     ```python
     padding.PSS(
         mgf=padding.MGF1(hashes.SHA256()),
         salt_length=padding.PSS.MAX_LENGTH
     )
     ```

3. **密钥长度**：
   - 至少使用 2048 位，推荐 3072 或 4096 以应对未来威胁。

4. **避免直接加密大数据**：
   - RSA 不适合直接加密大量数据。
   - 应结合 AES 等对称加密使用“混合加密”方案。

---

## 📚 参考资料

- [cryptography 官方文档](https://cryptography.io/en/latest/)
- [OpenSSH Key Format](https://github.com/openssh/openssh-portable/blob/master/PROTOCOL.key)
- RFC 8017 — PKCS #1 v2.2
- NIST FIPS 186-4 — Digital Signature Standard (DSS)

---

## 🧾 版本信息

- **语言**: Python 3.6+
- **库版本要求**: `cryptography >= 3.0`
- **许可证**: MIT（示例代码，实际请根据项目授权）

---

> ✅ 本文档最后更新：2025年4月5日  
> 作者：AI Assistant  
> 用途：开发参考、API 文档、安全实践指南