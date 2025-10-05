# `DataEncoder` 技术文档

```markdown
# DataEncoder - 安全数据编码与解码模块

## 概述

`DataEncoder` 是一个用于安全传输数据的 Python 类，提供数据加密、签名、压缩和结构化打包功能。它结合了 **RC4 对称加密** 和 **RSA 非对称加密**，确保数据在传输过程中的机密性、完整性和身份验证。

该类适用于点对点通信场景，支持动态获取对方公钥，并使用本地私钥进行签名，接收方通过公钥验证签名并解密数据。

---

## 依赖说明

### 第三方库
- `ujson`（可选）：高性能 JSON 库，若不可用则回退至标准库 `json`
- `zlib`：内置，用于数据压缩
- `struct`：内置，用于二进制数据打包/解包

### 内部模块
- `appPublic.rsawrap.RSA`：封装 RSA 加密/解密、签名/验签功能
- `appPublic.rc4.RC4`：实现 RC4 流加密算法
- `appPublic.uniqueID.getID`：生成唯一 ID（用作 RC4 密钥）

> 注：未启用 Brotli 压缩（相关导入被注释）

---

## 核心常量

| 常量 | 值 | 含义 |
|------|----|------|
| `DATA_TYPE_BYTES` | `1` | 数据类型为原始字节流 |
| `DATA_TYPE_STR`   | `2` | 数据类型为字符串（UTF-8 编码） |
| `DATA_TYPE_JSON`  | `3` | 数据类型为 JSON 对象（序列化后为 UTF-8 字节） |

---

## `DataEncoder` 类定义

### 初始化方法：`__init__(self, myid, func_get_peer_pubkey, private_file=None)`

#### 参数：
| 参数名 | 类型 | 描述 |
|--------|------|------|
| `myid` | str 或 any | 当前节点的唯一标识符 |
| `func_get_peer_pubkey` | callable | 回调函数，用于根据 `peer_id` 获取对方公钥 |
| `private_file` | str, optional | 私钥文件路径；若未提供，则自动生成新密钥对 |

#### 功能：
- 创建或加载 RSA 密钥对（私钥 + 公钥）
- 初始化内部状态：
  - `self.public_keys`: 缓存其他节点的公钥
  - `self.rsa`, `self.rc4`: 实例化加解密工具

#### 示例回调函数签名：
```python
def get_pubkey(peer_id):
    # 返回对应的 RSA 公钥对象
    return rsa_public_key_obj
```

---

## 核心方法

### `identify_datatype(data)`
自动识别输入数据类型并转换为字节格式。

#### 返回值：
元组 `(data_type, encoded_bytes)`  
其中 `data_type` 为上述三种之一。

| 输入类型 | 输出类型 | 处理方式 |
|---------|----------|--------|
| `bytes` | `DATA_TYPE_BYTES` | 直接返回 |
| `str`   | `DATA_TYPE_STR`   | `.encode('utf-8')` |
| 其他（如 dict/list） | `DATA_TYPE_JSON` | `json.dumps().encode('utf-8')` |

---

### `pack(peer_id, data, uncrypt=False)`
将数据加密、签名并打包成安全格式发送给指定 `peer_id`。

#### 参数：
| 参数 | 描述 |
|------|------|
| `peer_id` | 接收方的身份 ID |
| `data` | 待发送的数据（任意类型） |
| `uncrypt` | 是否跳过加密（调试用途），仅压缩不加密 |

#### 打包流程：

1. 调用 `identify_datatype(data)` 获取类型和字节数据。
2. 若 `uncrypt=True`，直接构造明文包并返回压缩结果。
3. 否则：
   - 生成随机 RC4 密钥（`getID()`）
   - 使用接收方公钥加密该密钥（RSA 加密）
   - 使用 RC4 加密原始数据
   - 构造 struct 格式字符串（含长度信息）
   - 将以下字段按顺序打包：
     1. **格式头（18字节）**：描述后续结构
     2. **数据类型（1字节）**
     3. **加密后的数据**
     4. **加密后的 RC4 密钥**
     5. **数字签名（覆盖以上所有内容）**
   - 使用 `zlib.compress()` 压缩整个包
   - 返回压缩后的二进制数据

#### 结构体格式示例：
假设加密数据长 1024 字节，密钥长 256 字节，则格式为：
```
'18s b1024s256s256s'
```
最后一个 `256s` 是签名（固定长度由 RSA 决定）。

> 签名范围包括：头部 + 类型 + 加密数据 + 加密密钥

---

### `unpack(peer_id, data)`
解包并还原从 `peer_id` 收到的安全数据。

#### 参数：
| 参数 | 描述 |
|------|------|
| `peer_id` | 发送方的身份 ID |
| `data` | 接收到的压缩二进制数据 |

#### 解包流程：

1. 解压 `zlib.decompress(data)`
2. 判断是否为无加密模式（前 18 字节全为 `\x00`）：
   - 是 → 按简单格式解析（仅类型+数据），返回明文
3. 否则进入安全解包流程：
   - 提取前 18 字节作为格式字符串（去除尾部 `\x00`）
   - 解析剩余数据得到：类型、加密数据、加密密钥、签名
   - 验证签名（使用发送方公钥）
   - 若失败 → 抛出异常 `'data sign verify failed'`
   - 成功后：
     - 用本机私钥解密 RC4 密钥
     - 用 RC4 解密数据
     - 根据类型还原为原始数据（bytes / str / json）
   - 返回解码后的原始数据

---

### 加解密辅助方法

| 方法 | 功能 |
|------|------|
| `encode_data(peer_pubkey, data)` | 使用 RC4 加密数据，RSA 加密密钥 |
| `decode_data(data, encoded_key)` | RSA 解密密钥，再用 RC4 解密数据 |
| `sign_data(data)` | 使用本机私钥对数据签名 |
| `verify_sign(data, sign, pubkey)` | 使用对方公钥验证签名有效性 |

---

### 公钥管理方法

| 方法 | 功能 |
|------|------|
| `my_text_publickey()` | 获取本机公钥的文本表示（Base64 编码等） |
| `get_peer_pubkey(peer_id)` | 获取某 peer 的公钥（缓存或调用回调函数） |
| `set_peer_pubkey(peer_id, pubkey)` | 设置某 peer 的公钥对象 |
| `set_peer_text_pubkey(peer_id, text_pubkey)` | 从文本形式设置公钥（自动解析） |
| `get_peer_text_pubkey(peer_id)` | 获取某 peer 的公钥文本形式（需已存在） |
| `exist_peer_publickeys(peer_id)` | 查询是否已有某 peer 的公钥 |

---

## 数据格式详解

### 安全包结构（压缩前）

| 偏移 | 字段 | 长度 | 说明 |
|------|------|-------|------|
| 0    | 格式描述字符串 | 18 字节 | 如 `'b1024s256s256s\x00...'` |
| 18   | 数据类型 | 1 字节 | `1=bytes`, `2=str`, `3=json` |
| 19   | 加密数据 | 可变 | RC4 加密后的 payload |
| 19+len(d) | 加密密钥 | 可变 | RSA 加密后的 RC4 密钥 |
| ...  | 数字签名 | 固定（如 256） | RSA-PKCS1-V1_5 签名 |

> 总长度 = 18 + len(d) + len(k) + len(s)

### 明文包结构（`uncrypt=True`）

| 偏移 | 字段 | 长度 | 说明 |
|------|------|-------|------|
| 0    | 填充零 | 18 字节 | 全 `\x00` 表示无加密 |
| 18   | 数据类型 | 1 字节 | 同上 |
| 19   | 原始数据 | 可变 | 未经加密 |

---

## 使用示例

### 初始化
```python
def fetch_pubkey(pid):
    # 实现获取 peer 公钥逻辑
    return rsa_pubkey_obj

encoder = DataEncoder(
    myid="node_A",
    func_get_peer_pubkey=fetch_pubkey,
    private_file="private.key"  # 或 None 自动生成
)
```

### 发送加密数据
```python
msg = {"cmd": "hello", "time": 123}
packed_data = encoder.pack("node_B", msg)
# 发送 packed_data 到 node_B
```

### 接收并解密
```python
received_data = ...  # 来自网络的数据
decoded_msg = encoder.unpack("node_A", received_data)
print(decoded_msg)  # {'cmd': 'hello', 'time': 123}
```

### 设置远程公钥（手动）
```python
pubkey_text = "-----BEGIN PUBLIC KEY-----\n..."  # PEM 或 Base64 文本
encoder.set_peer_text_pubkey("node_C", pubkey_text)
```

---

## 注意事项

1. **安全性提醒**：
   - RC4 已被认为不安全，建议在非敏感环境使用或替换为 AES。
   - RSA 密钥长度应 ≥ 2048 bits。
   - 签名防止篡改，但不防重放攻击，需上层协议补充 nonce/timestamp。

2. **性能优化**：
   - 使用 `ujson` 提升 JSON 序列化速度。
   - zlib 压缩有效减少传输体积。

3. **错误处理**：
   - 无法获取公钥时会抛出异常。
   - 签名验证失败也会中断流程。

4. **扩展建议**：
   - 支持 Brotli 压缩以进一步减小体积（当前代码中被注释）。
   - 添加 TTL、nonce、版本号等元数据字段。

---

## 辅助函数：`quotedstr(s)`

将字符串中的特殊字符转义，主要用于日志输出或字符串嵌入。

### 转义规则：
| 原字符 | 替换为 |
|--------|--------|
| `"`    | `\"`   |
| `\n`   | `\\n`  |

> 其他字符保持不变

### 示例：
```python
quotedstr('He said: "Hello\nWorld"')
# 输出: He said: \"Hello\\nWorld\"
```

---

## 版本信息
- 作者：Auto-generated from source
- 最后更新：根据所提供代码生成
- 许可：请参考项目整体 LICENSE
```