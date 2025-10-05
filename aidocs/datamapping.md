# `dataMapping` 模块技术文档

## 概述

`dataMapping` 模块提供两个核心函数：`keyMapping` 和 `valueMapping`，用于对字典数据进行键映射和值映射操作。该模块适用于数据转换、字段重命名、枚举值替换等常见场景。

依赖：
- `DictObject` 来自 `appPublic.dictObject`，用于将结果封装为对象形式（支持属性访问）。

---

## 函数说明

### 1. `keyMapping(dic, mappingtab, keepmiss=True)`

#### 功能
根据提供的映射表 `mappingtab` 将输入字典 `dic` 的键（keys）进行重命名，并返回新的字典。

#### 参数
| 参数名      | 类型       | 说明 |
|-----------|----------|------|
| `dic`       | `dict`     | 输入的原始字典 |
| `mappingtab` | `dict`     | 键映射表，格式为 `{旧键: 新键}` |
| `keepmiss`   | `bool`     | 是否保留未在 `mappingtab` 中定义的原始键。默认为 `True` |

#### 返回值
- `dict`：新字典，其键已根据 `mappingtab` 映射为新名称。
- 若某键不在 `mappingtab` 中且 `keepmiss=True`，则保留原键；否则忽略该键。

#### 映射规则
- 对于每个键 `k` in `dic`：
  - 如果 `k` 在 `mappingtab` 中，则使用 `mappingtab[k]` 作为新键。
  - 否则，若 `keepmiss=True`，保留原键 `k`；若 `keepmiss=False`，则跳过此键。

#### 示例

```python
data = {'a1': 10, 'a2': 20, 'other': 99}
mapping = {'a1': 'b1', 'a2': 'b2'}

result = keyMapping(data, mapping)
# 输出: {'b1': 10, 'b2': 20, 'other': 99}

result = keyMapping(data, mapping, keepmiss=False)
# 输出: {'b1': 10, 'b2': 20}
```

#### 注意事项
- 使用 `mappingtab.get(k, k)` 实现默认保持原键不变的行为。
- 内部通过列表推导与 `dict.update()` 构建结果字典。

---

### 2. `valueMapping(dic, mappingtab)`

#### 功能
根据 `mappingtab` 对字典中指定字段的值进行映射转换，常用于枚举值或代码转义。

#### 参数
| 参数名       | 类型       | 说明 |
|------------|----------|------|
| `dic`        | `dict`     | 输入字典 |
| `mappingtab`  | `dict`     | 值映射表，结构为 `{字段名: {原值: 目标值, "__default__": 默认值}}` |

#### 返回值
- `DictObject`：映射后的结果字典被封装成 `DictObject` 对象，支持属性访问（如 `obj.field1`）。

#### 映射规则
对于 `dic` 中的每一个键 `k`：
- 查找 `mappingtab[k]` 是否存在：
  - 若不存在，则保留原值。
  - 若存在，则查找 `dic[k]` 对应的目标值：
    - 若目标值存在，赋值；
    - 否则使用 `mappingtab[k].get('__default__', dic[k])` 作为默认值。

> 特殊键 `"__default__"` 可定义默认映射值。若未设置，默认为原始值。

#### 示例

```python
data = {'status': 'A', 'type': 'X', 'name': 'test'}
mapping = {
    'status': {
        'A': 'Active',
        'I': 'Inactive',
        '__default__': 'Unknown'
    },
    'type': {
        'X': 'External',
        'I': 'Internal'
        # 无 __default__
    }
}

result = valueMapping(data, mapping)
# result 是 DictObject，内容如下：
# {
#   'status': 'Active',
#   'type': 'External',
#   'name': 'test'  # 不在 mappingtab 中，原样保留
# }

# 访问方式：
# result.status => 'Active'
# result.type   => 'External'
```

另一个例子：

```python
data = {'level': 'unknown'}
mapping = {
    'level': {
        'high': 'H',
        'low': 'L',
        '__default__': 'N/A'
    }
}

result = valueMapping(data, mapping)
# result.level => 'N/A'
```

#### 注意事项
- 所有未在 `mappingtab` 中列出的字段均保持原值。
- `__default__` 提供了灵活的兜底机制，增强健壮性。
- 最终返回的是 `DictObject(**ret)`，允许以点语法访问属性。

---

## 使用建议

- **`keyMapping`** 适合用于 API 数据结构调整、数据库字段到模型字段的映射。
- **`valueMapping`** 适合处理状态码、类型编码、国际化标签转换等场景。
- 结合两者可实现完整的数据清洗与标准化流程。

---

## 依赖说明

本模块依赖：
```python
from appPublic.dictObject import DictObject
```
确保环境中已安装并可导入 `appPublic` 包。`DictObject` 支持动态属性访问，提升代码可读性和便利性。

---

## 版本信息

- 创建时间：未知
- 最后更新：根据代码逻辑整理
- 维护者：开发者团队

--- 

📌 **提示**：在实际项目中建议添加类型注解和异常处理以增强稳定性。