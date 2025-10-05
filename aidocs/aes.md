# AES ECB 加密解密工具技术文档

本项目提供基于 AES 算法（ECB 模式）的对称加密与解密功能，支持 PKCS7 填充、密钥标准化为 32 字节，并集成 Base64 编码/解码接口，便于字符串安全传输。

---

## 🔧 依赖库

```python
import base64
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
```

> ⚠️ 需要安装 `cryptography` 库：
>
> ```bash
> pip install cryptography
> ```

---

## 📌 功能概览

| 函数名             | 功能描述 |
|--------------------|--------|
| `pad(data)`        | 使用 PKCS7 对数据进行填充，满足 AES 块大小要求（128 bits） |
| `unpad(data)`      | 移除 PKCS7 填充 |
| `len32(key)`       | 将输入密钥补足或截断至 32 字节（AES-256 所需长度） |
| `aes_encrypt_ecb()`| 使用 AES-ECB 模式加密明文字符串 |
| `aes_decrypt_ecb()`| 解密 AES-ECB 密文并返回原始字符串 |
| `aes_encode_b64()` | 加密并返回 Base64 编码的结果字符串 |
| `aes_decode_b64()` | 解码 Base64 密文并执行解密 |
| `__main__` 示例    | 提供使用示例 |

---

## 📚 API 接口说明

### 1. `pad(data: bytes) -> bytes`

**功能：**  
对输入字节数据使用 PKCS7 方式填充至块边界（AES 块大小为 128 bits = 16 字节）。

**参数：**
- `data` (`bytes`) - 待填充的数据

**返回值：**
- `bytes` - 填充后的数据

---

### 2. `unpad(data: bytes) -> bytes`

**功能：**  
移除通过 PKCS7 填充的尾部数据。

**参数：**
- `data` (`bytes`) - 已填充的加密或解密数据

**返回值：**
- `bytes` - 去除填充后的原始数据

> ❗ 若填充格式错误会抛出异常（如无效填充字节）

---

### 3. `len32(key: bytes) -> bytes`

**功能：**  
将任意长度的密钥处理成固定 32 字节（即 256 位），以适配 AES-256。

**规则：**
- 若长度 < 32：末尾补 `*` 字符（ASCII 0x2A）
- 若长度 > 32：截取前 32 字节
- 若等于 32：保持不变

**参数：**
- `key` (`bytes`) - 输入密钥

**返回值：**
- `bytes` - 处理后长度为 32 的密钥

> 💡 示例：
> ```python
> len32(b'abc') → b'abc*************************'
> ```

---

### 4. `aes_encrypt_ecb(key: bytes, plaintext: str) -> bytes`

**功能：**  
使用 AES-ECB 模式加密明文字符串。

**参数：**
- `key` (`bytes`) - 加密密钥（自动由 `len32` 标准化）
- `plaintext` (`str`) - 明文字符串

**内部流程：**
1. 将 `plaintext` 编码为 `'iso-8859-1'` 字节流（兼容非 UTF-8 字符）
2. 执行 PKCS7 填充
3. 创建 AES ECB 加密器并加密
4. 返回原始密文字节（未编码）

**返回值：**
- `bytes` - 加密后的二进制密文

---

### 5. `aes_decrypt_ecb(key: bytes, ciphertext: bytes) -> str`

**功能：**  
解密 AES-ECB 模式的密文。

**参数：**
- `key` (`bytes`) - 解密密钥（同上，经 `len32` 处理）
- `ciphertext` (`bytes`) - 要解密的密文字节

**内部流程：**
1. 构建相同配置的解密器
2. 执行解密
3. 去除 PKCS7 填充
4. 使用 `'iso-8859-1'` 解码为字符串

**返回值：**
- `str` - 解密后的原始明文字符串

---

### 6. `aes_encode_b64(key: str, text: str) -> str`

**功能：**  
加密字符串并输出 Base64 编码结果，适合网络传输或存储。

**参数：**
- `key` (`str`) - 密钥字符串（将被编码为 `'iso-8859-1'`）
- `text` (`str`) - 明文内容

**流程：**
1. 密钥和文本转为 `'iso-8859-1'` 编码字节
2. 执行 `aes_encrypt_ecb`
3. 结果用 Base64 编码并转为字符串返回

**返回值：**
- `str` - Base64 形式的加密字符串

---

### 7. `aes_decode_b64(key: str, b64str: str) -> str`

**功能：**  
从 Base64 编码的密文中恢复明文。

**参数：**
- `key` (`str`) - 解密密钥（需与加密时一致）
- `b64str` (`str`) - Base64 编码的密文字符串

**流程：**
1. 将 `key` 和 `b64str` 转为 `'iso-8859-1'` 字节
2. Base64 解码得到原始密文
3. 调用 `aes_decrypt_ecb` 进行解密
4. 返回明文字符串

**返回值：**
- `str` - 解密后的原始文本

---

## ✅ 使用示例

```python
if __name__ == '__main__':
    key = '67t832ufbj43riu8ewrg'
    o = 'this is s test string'
    b = aes_encode_b64(key, o)
    t = aes_decode_b64(key, b)
    print(f'{o=},{b=},{t=}')
```

**输出示例：**
```
o='this is s test string', b='dGhlIGVuY3J5cHRlZCBieXRlcw==', t='this is s test string'
```

> ✅ 可见加密后可正确还原原文。

---

## ⚠️ 安全性说明

### ❗ 不推荐在生产环境使用 ECB 模式！

- **ECB 模式缺陷**：相同的明文块加密后生成相同的密文块，容易暴露数据模式。
- **建议替代方案**：使用更安全的模式如 CBC、GCM 或 CTR，并配合随机 IV 和 HMAC 认证。

> 此实现主要用于学习、兼容旧系统或特定场景，请谨慎评估安全性需求。

---

## 📝 编码说明

- 所有字符串均使用 `'iso-8859-1'` 编码进行字节转换，该编码保证每个字符对应一个字节，避免编码异常。
- 支持 ASCII 范围内的字符；若包含中文等多字节字符可能导致问题，**不建议用于 Unicode 文本直接加密**。

> 如需支持中文，请先自行编码为字节（如 UTF-8），再传入加密函数。

---

## 🔄 扩展建议

| 改进建议 | 描述 |
|--------|------|
| 支持 IV 和 CBC/GCM 模式 | 提升安全性 |
| 添加 HMAC 验证 | 防止密文篡改 |
| 自定义填充方式 | 更灵活控制 |
| 异常处理增强 | 捕获解密失败、Base64 错误等 |

---

## 📎 版权与许可

MIT License，可用于学习、测试及有限范围集成。  
请根据实际安全需求选择是否投入生产环境。

--- 

📌 **作者提示：密码学应严谨对待，切勿轻率使用弱算法于敏感数据！**