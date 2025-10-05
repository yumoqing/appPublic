# 技术文档：JSON 编码与解码工具模块

本模块提供了一组用于处理 Python 数据结构的 JSON 序列化与反序列化工具函数，支持 Unicode 转换、统一编码处理以及标准化的响应格式封装。

---

## 目录

- [功能概述](#功能概述)
- [函数说明](#函数说明)
  - [`uni_str(a, encoding)`](#uni_stra-encoding)
  - [`success(data)`](#successdata)
  - [`error(errors)`](#errorerrors)
  - [`jsonEncode(data, encode='utf-8')`](#jsonencodedata-encodeutf-8)
  - [`jsonDecode(jsonstring)`](#jsondecodejsonstring)
- [使用示例](#使用示例)
- [注意事项](#注意事项)

---

## 功能概述

该模块主要实现以下功能：

1. **统一字符串编码转换**（`uni_str`）：将任意嵌套数据结构中的字符串递归转换为 Unicode 字符串（Python 2 环境下），确保编码一致性。
2. **标准响应构造**：提供 `success()` 和 `error()` 函数以返回统一格式的成功/错误响应对象。
3. **安全的 JSON 序列化与反序列化**：通过 `jsonEncode` 和 `jsonDecode` 实现对复杂数据类型的兼容性处理。

> ⚠️ 注意：此代码适用于 **Python 2** 环境（使用了 `unicode` 类型）。在 Python 3 中需进行相应调整。

---

## 函数说明

### `uni_str(a, encoding)`

递归地将输入数据结构中所有字符串转换为指定编码的 Unicode 字符串。

#### 参数
| 参数 | 类型 | 描述 |
|------|------|------|
| `a` | 任意类型 | 输入的数据对象（如 str、dict、list、bool 等） |
| `encoding` | str | 字符串编码方式，默认通常为 `'utf-8'` |

#### 返回值
返回一个与输入结构相同但所有字符串均为 Unicode 类型的对象。

#### 处理逻辑
| 输入类型 | 处理方式 |
|---------|----------|
| `None` | 返回 `None` |
| `list` 或 `tuple` | 遍历每个元素并递归调用 `uni_str`，返回新列表或元组 |
| `dict` | 遍历键值对，分别对键和值递归处理，返回新字典 |
| `bool` | 直接返回原值（不转换） |
| `unicode` | 已是 Unicode，直接返回 |
| `str` 或具有 `__str__` 方法的对象 | 调用 `str()` 并使用指定编码解码为 `unicode` |
| 其他类型（int、float 等） | 直接返回原值 |

#### 示例
```python
uni_str("hello", "utf-8")  # 输出: u'hello'
uni_str({"name": "张三"}, "utf-8")  # 输出: {u'name': u'\u5f20\u4e09'}
```

---

### `success(data)`

构造一个表示操作成功的标准响应对象。

#### 参数
| 参数 | 类型 | 描述 |
|------|------|------|
| `data` | 任意可序列化对象 | 成功时返回的数据内容 |

#### 返回值
```json
{
  "success": true,
  "data": data
}
```

#### 示例
```python
success({"id": 1, "name": "Alice"})
# 输出: {'success': True, 'data': {'id': 1, 'name': 'Alice'}}
```

---

### `error(errors)`

构造一个表示操作失败的标准错误响应对象。

#### 参数
| 参数 | 类型 | 描述 |
|------|------|------|
| `errors` | list/dict/str | 错误信息，可以是字符串、列表或字典形式的错误描述 |

#### 返回值
```json
{
  "success": false,
  "errors": errors
}
```

#### 示例
```python
error("用户名不能为空")
# 输出: {'success': False, 'errors': '用户名不能为空'}

error(["字段A无效", "字段B缺失"])
# 输出: {'success': False, 'errors': ['字段A无效', '字段B缺失']}
```

---

### `jsonEncode(data, encode='utf-8')`

将任意 Python 对象安全地编码为 JSON 字符串。

#### 参数
| 参数 | 类型 | 描述 |
|------|------|------|
| `data` | 任意对象 | 待序列化的数据 |
| `encode` | str | 编码格式，默认为 `'utf-8'` |

#### 流程
1. 使用 `uni_str(data, encode)` 将所有字符串转换为 Unicode。
2. 使用 `json.dumps()` 将处理后的数据序列化为 JSON 字符串。

#### 返回值
- 类型：`str`
- 内容：合法的 JSON 格式字符串

#### 示例
```python
jsonEncode({"msg": "你好世界"})  
# 输出: '{"msg": "\\u4f60\\u597d\\u4e16\\u754c"}'
```

---

### `jsonDecode(jsonstring)`

将 JSON 字符串解析为 Python 对象。

#### 参数
| 参数 | 类型 | 描述 |
|------|------|------|
| `jsonstring` | str | 合法的 JSON 字符串 |

#### 返回值
- 解析后的 Python 对象（dict、list、str、int 等）

#### 异常处理
- 若输入不是合法 JSON，会抛出 `ValueError`（由 `json.loads` 抛出）

#### 示例
```python
jsonDecode('{"name": "Bob", "age": 30}')
# 输出: {u'name': u'Bob', u'age': 30}
```

---

## 使用示例

```python
# 构造成功响应并编码为 JSON
response = success({"user_id": 123, "username": "test_user"})
json_str = jsonEncode(response)
print(json_str)
# 输出: {"success": true, "data": {"user_id": 123, "username": "test_user"}}

# 解码 JSON 字符串
decoded = jsonDecode(json_str)
print(decoded['data']['username'])  # 输出: test_user

# 构造错误响应
err_resp = error(["密码太短", "邮箱格式错误"])
err_json = jsonEncode(err_resp)
print(err_json)
# 输出: {"success": false, "errors": ["密码太短", "邮箱格式错误"]}
```

---

## 注意事项

1. **Python 版本兼容性**
   - 此代码基于 **Python 2** 设计（依赖 `unicode` 类型）。
   - 在 **Python 3** 中，`unicode` 应替换为 `str`，`str` 替换为 `bytes`，建议重写以适配 Python 3 的字符串模型。

2. **性能考虑**
   - `uni_str` 是递归函数，对于深度嵌套或大型数据结构可能影响性能。
   - 建议仅在必要时使用，或考虑缓存机制优化。

3. **安全性**
   - `jsonDecode` 不做额外校验，请确保输入来源可信，防止注入攻击。

4. **编码假设**
   - 所有字符串预期使用 UTF-8 编码。若传入其他编码（如 GBK），需确保数据真实编码匹配。

5. **对象方法调用风险**
   - 在 `uni_str` 中调用了 `getattr(a, '__str__')` 并执行 `str(a)`，应确保对象的 `__str__` 方法无副作用。

---

## 版本信息

- 兼容环境：Python 2.x
- 依赖库：`json`（标准库）

> ✅ 推荐用于需要统一响应格式与编码处理的传统 Web API 后端项目（如 Django 1.x / Flask 配合 Python 2）。