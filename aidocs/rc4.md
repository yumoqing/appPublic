# RC4 加密与密钥链技术文档

---

## 概述

本文档详细描述了一个基于 **RC4 流加密算法** 和动态密钥生成机制（`KeyChain`）的 Python 实现。该系统支持数据加解密、自动密钥轮换、时间敏感的密钥管理，并具备一定的容错能力以应对时钟偏差。

主要特性包括：

- 使用 RC4 算法进行流加密
- 引入随机盐值（salt）和 SHA-1 密钥扩展增强安全性
- 支持 Base64 编码输出
- 动态密钥生成（基于时间窗口）
- 容忍一定时间偏移的解密尝试（前向/后向周期补偿）

---

## 依赖模块

```python
import time
import datetime
import random
import base64
from hashlib import sha1
```

> 注：`random` 模块当前未使用，可能是预留或冗余导入。

---

## 核心类说明

### 1. `RC4` 类 —— RC4 加密器

#### 初始化方法：`__init__(self, data_coding='utf8')`

初始化 RC4 加密实例。

| 参数         | 类型   | 描述 |
|--------------|--------|------|
| `data_coding` | str    | 数据编码格式，默认为 `'utf8'`，用于字符串与字节之间的转换 |

##### 属性：
- `bcoding`: 内部字节编码，固定为 `'iso-8859-1'`（确保字节范围兼容）
- `dcoding`: 外部数据编码（默认 UTF-8）
- `salt`: 固定盐值 `b'AFUqx9WZuI32lnHk'`（16 字节），用于密钥强化

---

#### 私有方法：`_crypt(self, data: bytes, key: bytes) -> bytes`

执行标准 RC4 加密/解密操作。

##### 参数：
- `data`: 待处理的字节数据
- `key`: 密钥（bytes）

##### 返回：
- 加密或解密后的字节串（经 `'iso-8859-1'` 编码）

##### 算法流程：
1. 初始化长度为 256 的 S-box。
2. 使用密钥调度算法（KSA）打乱 S-box。
3. 使用伪随机生成算法（PRGA）逐字节异或加密。

> ⚠️ 注意：此实现中返回的是 `.join(chr(...))` 后再 `.encode('iso-8859-1')`，需注意字符边界问题。

---

#### 方法：`encode_bytes(self, bdata: bytes, key: bytes) -> bytes`

对字节数据执行带盐值的加密。

##### 流程：
1. 计算密钥摘要：`sha1(key + self.salt).digest()`
2. 使用上述密钥对 `bdata` 执行 `_crypt`
3. 将原始 salt 前缀附加到密文前（共 16 字节）

##### 返回：
- `salt + encrypted_data`（bytes）

---

#### 方法：`encode(self, data: str/bytes, key: str, encode=base64.b64encode) -> str`

高层加密接口，支持字符串输入和最终编码。

##### 参数：
- `data`: 明文（字符串或字节）
- `key`: 密钥（字符串）
- `encode`: 可选编码函数（如 `base64.b64encode`），设为 `None` 则不编码

##### 行为：
- 若 `data` 是字符串，则按 `dcoding` 编码为字节
- 调用 `encode_bytes` 加密
- 若指定 `encode` 函数，则对结果进行编码（如 Base64）
- 返回编码后的字符串（UTF-8 解码）

> ✅ 示例：
> ```python
> rc = RC4()
> code = rc.encode("hello", "mykey")
> ```

---

#### 方法：`decode_bytes(self, data: bytes, key: bytes) -> bytes`

解密由 `encode_bytes` 生成的数据。

##### 步骤：
1. 提取前 16 字节作为 salt（但实际未使用！应为 bug？）
2. 使用 `sha1(key + self.salt)` 生成密钥
3. 对剩余部分调用 `_crypt` 解密

> ❗⚠️ Bug 提示：虽然提取了 salt，但在密钥生成中仍使用固定的 `self.salt`，而非从输入读取的 salt。这导致无法正确处理不同 salt 的情况。

##### 返回：
- 解密后的原始数据（bytes）

---

#### 方法：`decode(self, data: str/bytes, key: str, decode=base64.b64decode) -> str`

高层解密接口。

##### 参数：
- `data`: 已加密并可选编码过的数据
- `key`: 解密密钥
- `decode`: 解码函数（默认 Base64）

##### 行为：
- 若 `data` 是字符串，先用 `dcoding` 编码成字节
- 若 `decode` 存在，先解码（如 Base64 解码）
- 调用 `decode_bytes` 解密
- 结果以 `dcoding` 解码为字符串返回

> ✅ 示例：
> ```python
> text = rc.decode(code, "mykey")
> ```

---

### 2. `KeyChain` 类 —— 时间同步密钥链

提供基于时间窗口的动态密钥管理和自动密钥匹配功能，适用于分布式环境下的安全通信。

#### 初始化：`__init__(seed_str, crypter=None, keylen=23, period=600, threshold=60, time_delta=0)`

| 参数        | 类型     | 默认值    | 说明 |
|-------------|----------|-----------|------|
| `seed_str`   | str/bytes | -         | 种子字符串，用于派生密钥 |
| `crypter`    | RC4 实例 | None      | 自定义加密器，若无则创建默认 RC4 |
| `keylen`     | int       | 23        | 生成密钥的字符长度 |
| `period`     | int       | 600       | 时间窗口周期（秒），即每 10 分钟换一次密钥 |
| `threshold`  | int       | 60        | 容差阈值（秒），判断是否接近周期边界 |
| `time_delta` | int       | 0         | 时间偏移量（可用于调试或校准） |

##### 内部属性：
- `keypool`: 缓存已生成的密钥 `{indicator: key}`
- `timezone`: 设置为 GMT 时区
- `indicator`: 当前时间所属的时间段起点（如每 600 秒一个区块）

---

#### 方法：`get_timestamp(self) -> int`

获取当前 Unix 时间戳（减去 `time_delta`）

---

#### 方法：`get_indicator(ts=None) -> int`

计算时间指示器（所在周期的起始时间）

例如：
- `period=600` → 每 10 分钟一个周期
- `ts=1712345678` → indicator = `(1712345678 // 600) * 600`

##### 返回：
- 当前时间所属周期的起始时间戳

---

#### 方法：`genKey(indicator) -> bytes`

根据 `indicator` 从 `seed_str` 生成唯一密钥。

##### 算法逻辑：
1. 若缓存中已有对应密钥，直接返回
2. 否则使用循环算法从 `seed_str` 中按规则选取字符构造密钥：
   - 初始值 `v = indicator`
   - 每次取 `j = v % keylen` 作为索引
   - 从 `seed_str[j]` 取字符追加
   - 更新 `v = v - (j + k1)*m + keylen`
   - 直到生成 `keylen` 长度的密钥
3. 缓存密钥，并清理过期条目（早于 `indicator - period` 的）

> 🔐 安全性：密钥依赖时间和种子，难以预测

---

#### 方法：`encode_bytes(bdata: bytes) -> bytes`

使用当前时间对应的密钥加密数据。

##### 流程：
1. 获取当前 `indicator`
2. 生成对应密钥 `key`
3. 构造明文：`key + bdata`（将密钥本身也加密传输）
4. 使用 `crypter.encode_bytes(data, key)` 加密

> 📦 输出结构：`salt + encrypted(key + bdata)`

---

#### 方法：`decode_bytes(data: bytes) -> bytes or None`

智能解密：尝试用当前、上一周期、下一周期的密钥解密。

##### 步骤：
1. 获取当前 `indicator` 和密钥
2. 尝试解密
3. 验证解密后数据前缀是否等于密钥（完整性校验）
4. 如果失败且接近周期底部（即将切换），尝试上一周期密钥
5. 如果接近顶部（刚过切换点），尝试下一周期密钥

##### 返回：
- 成功：解密后的原始数据（不含密钥头）
- 失败：`None`

---

#### 方法：`encode(text: str) -> bytes`

加密字符串版本，内部转为 UTF-8 字节后调用 `encode_bytes`

---

#### 方法：`decode(data: bytes) -> str or None`

解密并返回 UTF-8 字符串；若失败返回 `None`

---

## 辅助函数

### `password(pwdtxt: str, key=pwdkey) -> str or None`

使用固定密钥对密码文本加密并验证。

##### 步骤：
1. 加密 `pwdtxt`
2. 立即解密验证一致性
3. 一致则返回加密结果（Base64 编码字符串），否则返回 `None`

> ✅ 用途：确保加密过程可靠

---

### `unpassword(code: str, key=pwdkey) -> str or None`

解密由 `password()` 生成的密文。

##### 返回：
- 明文字符串 或 `None`

---

## 使用示例

```python
if __name__ == '__main__':
    data = b"231r3 feregrenerjk gkht324g8924gnfw ;ejkvwkjerv"
    key = b'123456'
    
    rc4 = RC4()
    kc = KeyChain('in the heaven, we are equal', rc4)

    print("原始数据:", data)

    # 加密
    encoded_data = kc.encode_bytes(data)
    print("加密后数据:", encoded_data, "长度:", len(encoded_data))

    # 解密
    decoded_data = kc.decode_bytes(encoded_data)
    print("解密数据:", decoded_data)
    print("解密成功:", decoded_data == data)
```

---

## 安全性分析

| 特性 | 评估 |
|------|------|
| **RC4 算法** | 已知存在弱点（如偏差输出），不推荐用于高安全场景 |
| **Salt 固定** | `self.salt` 固定可能导致重放攻击风险 |
| **密钥派生** | 自定义算法非标准，缺乏密码学证明 |
| **密钥包含在明文中加密** | 有一定防篡改作用，但仍可能被暴力破解 |
| **时间同步机制** | 适合短期令牌、API 认证等场景 |
| **Base64 支持** | 方便文本传输 |

> ✅ 推荐用途：轻量级认证令牌、会话加密、临时凭证  
> ❌ 不推荐：金融交易、长期存储加密

---

## 已知问题与改进建议

| 问题 | 描述 | 建议 |
|------|------|-------|
| ❗ Salt 未真正参与密钥派生 | `decode_bytes` 忽略传入 salt，始终用固定 salt | 应使用传入 salt 生成密钥 |
| ⚠️ `_crypt` 返回方式不安全 | 使用 `chr()` 可能超出 ASCII 范围引发错误 | 改为直接构建字节数组 |
| ⚠️ RC4 已过时 | 存在已知漏洞（如 WEP 攻击） | 替换为 AES-CTR 或 ChaCha20 |
| 🔒 自定义密钥生成算法 | 非标准化，可能存在碰撞或弱密钥 | 使用 HMAC-SHA256 等标准 KDF |
| 💤 时间依赖性强 | 严重依赖系统时间准确性 | 增加强时间验证或 NTP 校准提示 |

---

## 总结

本模块实现了一套基于 RC4 和时间窗口密钥链的安全通信原型，具备以下优点：

- 简洁易集成
- 支持自动密钥轮换
- 具备时间容忍机制
- 可用于短生命周期数据保护

建议在低风险场景中使用，并考虑升级至更现代的加密算法（如 AES-GCM 或 ChaCha20-Poly1305）以提升安全性。

--- 

> 文档版本：v1.0  
> 最后更新：2025-04-05