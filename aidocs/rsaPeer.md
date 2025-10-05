# `RSAPeer` 加密通信模块技术文档

## 概述

本模块提供基于 **RSA + RC4** 的混合加密机制，用于实现安全的点对点数据传输。通过使用 RSA 对称密钥加密、RC4 数据流加密以及数字签名验证，确保消息的机密性、完整性与身份认证。

主要功能包括：
- 使用接收方公钥加密会话密钥（RC4 Key）
- 使用随机生成的 RC4 密钥加密实际数据
- 发送方用私钥对会话密钥进行签名
- 接收方使用发送方公钥验证签名并解密数据

---

## 依赖库

```python
from appPublic.rsawrap import RSA
from appPublic.rc4 import RC4
try:
    import ujson as json
except ImportError:
    import json
import random
```

- `appPublic.rsawrap.RSA`: 提供 RSA 公私钥加解密和数字签名功能。
- `appPublic.rc4.RC4`: 实现 RC4 流密码算法，用于高效加密大数据。
- `ujson`: 可选高性能 JSON 库；若不可用则回退至标准库 `json`。
- `random`: 用于生成随机会话密钥。

---

## 核心类说明

### 1. `DeliverPacket`

封装要传输的数据包结构，包含发送者信息及加密三要素：密文、加密后的会话密钥、签名。

#### 属性
| 字段名   | 类型   | 描述 |
|----------|--------|------|
| `sender` | str    | 发送方标识 ID |
| `c`      | str    | 使用 RC4 加密后的密文 |
| `k`      | str    | 使用对方公钥加密的 RC4 会话密钥 |
| `s`      | str    | 会话密钥的数字签名（由发送方私钥签名） |

#### 方法

##### `__init__(self, sender, c, k, s)`
初始化数据包对象。

参数：
- `sender` (str): 发送方 ID
- `c` (str): 密文
- `k` (str): 加密后的会话密钥
- `s` (str): 数字签名

##### `pack(self)`
将当前对象序列化为 JSON 字符串。

返回值：
- `str`: JSON 格式的字符串表示

示例输出：
```json
{
  "sender": "john",
  "c": "aB3x...",
  "k": "mN9y...",
  "s": "zX8v..."
}
```

##### `unpack(self, body)`
从 JSON 字符串反序列化填充对象字段。

参数：
- `body` (str): JSON 格式字符串

⚠️ 注意：代码中存在 bug —— 访问 `d.sender` 而非 `d['sender']`，应统一使用字典访问方式。

修复建议：
```python
self.sender = d['sender']
```

---

### 2. `RSAPeer`

代表一个支持加密通信的对等节点（Peer），具备加密发送和解密接收的能力。

#### 构造函数：`__init__(self, myid, myPrikey, peerPubKey=None)`

参数：
- `myid` (str): 当前节点的唯一标识（如用户名或公钥指纹）
- `myPrikey` (str): 自己的 **私钥**
- `peerPubKey` (str, optional): 对方的 **公钥**；若未指定，则需动态获取（见 `getPeerPublicKey`）

内部初始化：
- `self.rsa = RSA()`：创建 RSA 工具实例

#### 私有方法：`_genSystematicKey(self)`

生成长度在 10~15 之间的随机字符串作为 RC4 会话密钥。

字符集包含：
```
abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890~!@#$%^&*
```

返回值：
- `str`: 随机生成的密钥字符串

> ⚠️ 名称 `_genSystematicKey` 存疑，“systematic” 不符合语义，建议改为 `_generateSessionKey`

#### 公共方法：`encode(self, text)`

加密一段明文，并打包成安全数据包。

##### 参数
- `text` (str): 待加密的原始文本

##### 处理流程
1. 构造内部数据结构：`{"id": self.myid, "data": text}`
2. 将其 JSON 序列化为明文
3. 调用 `_genSystematicKey()` 生成 RC4 会话密钥 `sk`
4. 使用 `sk` 初始化 RC4 加密器，加密明文 → 得到密文 `c`
5. 使用自己的私钥 `mypri` 对 `sk` 进行签名 → 得到签名 `s`
6. 使用对方公钥 `peerpub` 加密 `sk` → 得到加密后的密钥 `k`
7. 组装最终数据包 `{c, k, s}` 并转为 JSON 返回

##### 返回值
- `str`: JSON 格式的加密数据包
- 若 `peerPubKey` 未设置，则返回 `None`

##### 示例输出
```json
{
  "c": "eWVpaGVsbG9fd29ybGQ=",
  "k": "AQIDBAUGBwgJCgsMDQ4PEA==",
  "s": "ZGFzaGluZ3FpYW5nLmRldg=="
}
```

#### 公共方法：`decode(self, body)`

解密来自对端的加密数据包。

##### 参数
- `body` (str): 接收到的 JSON 加密数据包

##### 处理流程
1. 解析 JSON 得到 `c`, `k`, `s`
2. 使用自己私钥解密 `k` → 恢复会话密钥 `sk`
3. 使用 `sk` 初始化 RC4 解密器，解密 `c` → 得到中间 JSON 文本
4. 反序列化得到内部数据 `{"id": sender_id, "data": payload}`
5. 验证签名：
   - 若已知对方公钥：直接调用 `rsa.check_sign(peerpub, sk, signature)`
   - 否则调用 `getPeerPublicKey(id)` 动态获取公钥后再验证
6. 验签失败返回 `None`，成功则返回原始 `payload`

##### 返回值
- `str`: 解密后的原始数据内容
- `None`: 解密或验签失败

> ✅ 支持两种模式：
> - 固定对端公钥（预配置）
> - 动态查询公钥（适用于去中心化场景）

---

## 安全机制详解

| 安全目标       | 实现方式 |
|----------------|---------|
| **机密性**     | 使用 RC4 对称加密数据，会话密钥由 RSA 非对称加密保护 |
| **完整性**     | 会话密钥附带数字签名，防止篡改 |
| **身份认证**   | 签名只能由持有私钥的一方生成，接收方可通过公钥验证来源 |
| **前向安全性** | 每次通信使用新生成的随机会话密钥 |

---

## 使用示例（Main 测试代码分析）

```python
if __name__ == '__main__':
    r = RSA()
    mary_pri = r.create_privatekey()
    mary_pub = r.create_publickey(mary_pri)
    
    john_pri = r.create_privatekey()
    john_pub = r.create_publickey(john_pri)
    
    # 注意：此处参数顺序错误！
    john_rp = RSAPeer(john_pri, mary_pub)   # ❌ 应该是 (myid, myPrikey, peerPubKey)
    mary_rp = RSAPeer(mary_pri, john_pub)
    
    txt = '''hello python ...'''
    c = john_rp.encode(txt)
    newtxt = mary_rp.decode(c)
    
    print(txt)
    print('<===>')
    print(c)
    print('<===>')
    print(newtxt)
```

### ❗ Bug 提示

构造函数调用错误：

```python
RSAPeer(john_pri, mary_pub)
```

但定义是：

```python
def __init__(self, myid, myPrikey, peerPubKey=None):
```

所以正确写法应该是：

```python
john_rp = RSAPeer("john", john_pri, mary_pub)
mary_rp = RSAPeer("mary", mary_pri, john_pub)
```

否则 `myid` 被误设为私钥内容，会导致后续编码异常。

---

## 建议改进点

| 问题 | 建议 |
|------|------|
| `DeliverPacket.unpack()` 中 `d.sender` 写法错误 | 改为 `d['sender']` |
| `_genSystematicKey` 名称不准确 | 改为 `_generateSessionKey` |
| 构造函数参数顺序易错 | 建议使用关键字参数或重命名参数 |
| 缺少异常处理 | 增加 try-except 包裹关键操作 |
| RC4 已被认为不安全（尤其在 TLS 中弃用） | 在生产环境中考虑替换为 AES-GCM 或 ChaCha20-Poly1305 |
| 无 Base64 编码处理 | 若底层 API 要求二进制安全传输，应对 `c`, `k`, `s` 做 base64 编码 |

---

## 总结

该模块实现了轻量级的安全通信协议，适合用于小型系统或 IoT 设备间的点对点加密通信。结合了非对称加密的身份认证能力和对称加密的效率优势，结构清晰，易于扩展。

### 适用场景
- UDP 对等通信（如文档中提到的 UDP 协议）
- 分布式日志传输
- 内部微服务间安全信道
- 即时通讯基础组件

---

## 版本信息

- Python 版本：≥ 3.6（兼容性良好）
- 第三方依赖：`ujson`（可选）、自定义 `RSA` 与 `RC4` 模块
- 许可协议：请参考项目 LICENSE 文件

--- 

> 📌 文档维护建议：配合单元测试与接口文档进一步完善健壮性描述。