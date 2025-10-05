# `DictObject` 技术文档

```markdown
# DictObject - 字典对象封装库

`DictObject` 是一个轻量级的 Python 工具类，用于将字典（`dict`）转换为支持属性访问的对象，并提供丰富的数据操作、序列化与嵌套结构处理能力。它允许通过点号语法访问字典键值，同时保留了标准字典的操作接口。

---

## 目录

- [功能概览](#功能概览)
- [依赖说明](#依赖说明)
- [核心函数](#核心函数)
  - [`multiDict2Dict(md)`](#multidict2dictmd)
- [核心类](#核心类)
  - [`DictObject`](#dictobject)
  - [`DictObjectEncoder`](#dictobjectencoder)
- [工厂方法](#工厂方法)
  - [`dictObjectFactory(_klassName__, **kwargs)`](#dictobjectfactory_klassname__-kwargs)
- [使用示例](#使用示例)
- [注意事项](#注意事项)

---

## 功能概览

- 将普通字典转为可点式访问的 `DictObject` 对象。
- 支持嵌套字典、列表、元组自动转换。
- 提供类似字典的标准方法（如 `.items()`, `.get()`, `.pop()` 等）。
- 可过滤内置函数、方法等不可序列化的类型。
- 支持 JSON 序列化（配合 `DictObjectEncoder`）。
- 支持继承和动态子类查找的工厂模式创建实例。

---

## 依赖说明

```python
import json
from json import JSONEncoder
from inspect import ismethod, isfunction, isbuiltin, isabstract
```

- `json`: 用于 JSON 编码/解码。
- `JSONEncoder`: 自定义 JSON 编码器基类。
- `inspect` 模块：
  - `ismethod`, `isfunction`: 判断是否为方法或函数。
  - `isbuiltin`: 判断是否为内置函数。
  - `isabstract`: 判断是否为抽象方法（用于排除不可序列化对象）。

---

## 核心函数

### `multiDict2Dict(md)`

将可能包含重复键的多值字典（如 Web 表单提交中的 `MultiDict`）转换为标准字典。若某键对应多个值，则将其合并为列表。

#### 参数
| 参数 | 类型 | 说明 |
|------|------|------|
| `md` | `dict` 或 `MultiDict` | 输入字典，可能含有重复键 |

#### 返回值
- `dict`: 转换后的字典。若某个键有多个值，则其值为列表；否则保持原样。

#### 示例
```python
d = {'a': 1, 'b': 2, 'a': 3}
result = multiDict2Dict(d)
# result => {'a': [1, 3], 'b': 2}
```

#### 实现逻辑
- 遍历输入字典；
- 若键不存在，直接赋值；
- 若已存在且原值是列表，追加新值；
- 否则将原值和新值构造成列表。

---

## 核心类

### `DictObject`

一个可动态扩展、支持属性访问的字典封装类。

#### 初始化：`__init__(**kw)`
接受关键字参数初始化对象。

##### 参数
| 参数 | 类型 | 说明 |
|------|------|------|
| `**kw` | `dict` | 关键字参数集合 |

##### 行为
- 记录初始属性名到 `org_keys__`；
- 使用 `__DOitem(v)` 处理每个值（递归构建嵌套结构）；
- 调用 `update()` 更新内部 `__dict__`。

---

#### 属性访问：`__getattr__(name)`

当调用未定义属性时，尝试从 `_addon()` 中获取该键的值。

- 如果存在，返回对应值；
- 否则返回 `None`。

> ⚠️ 注意：这不会触发 `AttributeError`，需注意潜在静默失败问题。

---

#### 方法列表

| 方法 | 功能 |
|------|------|
| `update(kw)` | 更新对象属性（仅添加或修改非原始属性） |
| `_addon()` | 获取用户添加的所有属性组成的字典（排除构造时的原始属性） |
| `clear()` | 清除所有动态添加的属性 |
| `get(name, default=None)` | 获取指定属性，不存在返回默认值 |
| `pop(k, default=None)` | 删除并返回属性值 |
| `popitem()` | 删除并返回任意一个 (key, value) 对 |
| `items()` / `keys()` / `values()` | 返回动态属性的视图对象（类似字典） |
| `__getitem__(name)` | 支持 `obj['key']` 语法访问 |
| `__setitem__(name, value)` | 支持 `obj['key'] = value` 语法设置 |
| `__delitem__(key)` | 支持 `del obj['key']` 删除属性 |
| `__str__()` | 输出动态属性的字符串表示（即 `str(_addon())`） |
| `__expr__()` | ❌ 存在错误：应为 `__repr__`，当前实现无效 |
| `copy()` | 返回动态属性的浅拷贝字典 |
| `to_dict()` | 深度转换为纯 `dict`（移除不可序列化内容） |
| `dict_to_dict(dic)` | 递归转换字典，处理嵌套 `DictObject`、函数、内置对象等 |
| `array_to_dict(v)` | 递归转换数组/元组，跳过函数等不可序列化项 |
| `__DOArray(a)` | 将列表/元组中每一项用 `__DOitem` 处理 |
| `__DOitem(i)` | 根据输入类型决定是否转换为 `DictObject` 或递归处理 |

---

#### 特殊方法说明

##### `to_dict()` 与 `dict_to_dict()`
用于深度清理对象，生成可用于 JSON 序列化的纯净字典。

- 递归遍历嵌套结构；
- 自动识别并转换：
  - `DictObject` → 调用 `.to_dict()`
  - `dict` → 递归调用 `dict_to_dict`
  - `list/tuple` → 调用 `array_to_dict`
- 过滤以下类型（不包含在输出中）：
  - 内置函数（`__builtins__`）
  - 函数、方法、内建函数、抽象方法（使用 `inspect` 判断）

##### `__DOitem(i)`
对传入值进行类型判断并包装：

| 输入类型 | 处理方式 |
|--------|---------|
| `DictObject` | 直接返回 |
| `dict` | 过滤非字符串键后构造新的 `DictObject(**i)` |
| `list` 或 `tuple` | 转换为 `[ __DOitem(x) for x in i ]` |
| 其他 | 原样返回 |

> ⚠️ 异常处理：构造失败时打印调试信息并重新抛出异常。

---

#### 类方法

##### `@classmethod isMe(cls, name)`
判断类名是否等于 `'DictObject'`。

> 用于工厂函数中判断目标类。

---

### `DictObjectEncoder(JSONEncoder)`

自定义 JSON 编码器，用于将 `DictObject` 实例序列化为 JSON。

#### 方法：`default(o)`
重写 `JSONEncoder.default()`，返回对象的 `_addon()` 字典。

##### 示例
```python
obj = DictObject(name="Alice", age=30)
json_str = json.dumps(obj, cls=DictObjectEncoder)
# 输出: {"name": "Alice", "age": 30}
```

> ✅ 支持嵌套结构序列化（前提是已通过 `to_dict()` 处理干净）。

---

## 工厂方法

### `dictObjectFactory(_klassName__, **kwargs)`

根据类名字符串动态创建 `DictObject` 或其子类的实例。

#### 参数
| 参数 | 类型 | 说明 |
|------|------|------|
| `_klassName__` | `str` | 类名（如 `'DictObject'`） |
| `**kwargs` | `dict` | 构造参数 |

#### 返回值
- `DictObject` 或其子类的实例。

#### 内部函数：`findSubclass(_klassName__, klass)`
递归查找 `klass` 的所有子类中满足 `isMe(_klassName__)` 的类。

#### 流程
1. 若类名为 `'DictObject'`，直接返回 `DictObject(**kwargs)`；
2. 否则递归查找子类；
3. 找到则调用该子类构造函数；
4. 未找到仍返回 `DictObject` 实例；
5. 出错时打印日志并抛出异常。

> ✅ 支持插件式扩展：可通过继承 `DictObject` 并重写 `isMe()` 实现自定义类匹配。

---

## 使用示例

### 1. 基本用法：属性访问

```python
data = {'name': 'Bob', 'age': 25, 'city': 'Beijing'}
obj = DictObject(**data)

print(obj.name)           # Bob
print(obj['age'])         # 25
print(obj.get('city'))    # Beijing
```

### 2. 嵌套字典自动转换

```python
nested = {
    'user': {
        'id': 1,
        'profile': {'name': 'Alice', 'tags': ['dev', 'py']}
    }
}
obj = DictObject(**nested)
print(obj.user.profile.name)  # Alice
print(obj.to_dict())
# {'user': {'id': 1, 'profile': {'name': 'Alice', 'tags': ['dev', 'py']}}}
```

### 3. JSON 序列化

```python
import json
from dictObject import DictObject, DictObjectEncoder

obj = DictObject(title="My App", version=1.0)
json_str = json.dumps(obj, cls=DictObjectEncoder, indent=2)
print(json_str)
```

输出：
```json
{
  "title": "My App",
  "version": 1.0
}
```

### 4. 工厂模式创建对象

```python
# 假设有子类 MyData 继承 DictObject 并重写了 isMe()
class MyData(DictObject):
    @classmethod
    def isMe(cls, name):
        return name == 'MyData'

obj = dictObjectFactory('MyData', x=1, y=2)
print(type(obj))  # <class '__main__.MyData'>
```

---

## 注意事项

1. **`__expr__` 方法命名错误**
   - 正确应为 `__repr__`，当前 `__expr__` 不会被 Python 解释器调用。
   - 建议修复为：
     ```python
     def __repr__(self):
         return repr(self._addon())
     ```

2. **`__builtins__` 过滤不完全可靠**
   - 当前只检查键名为 `'__builtins__'`，建议增强检测逻辑。

3. **性能考虑**
   - 每次调用 `_addon()` 都会重新计算差异，频繁调用可能影响性能。
   - 可缓存结果或改用更高效的数据结构。

4. **异常处理**
   - `__DOitem` 中捕获异常后打印信息但继续抛出，适合开发调试。
   - 生产环境建议记录日志而非打印。

5. **线程安全性**
   - 未做线程安全设计，多线程环境下慎用共享实例。

6. **内存泄漏风险**
   - `org_keys__` 记录初始属性，若后续手动增删较多，可能导致 `_addon()` 判断不准。

---

## 总结

`DictObject` 是一个灵活实用的字典对象封装工具，适用于配置管理、API 数据解析、动态对象构建等场景。结合 `dictObjectFactory` 和 `DictObjectEncoder`，可实现高度可扩展的数据模型系统。

✅ 推荐用于快速原型开发、DSL 设计、Web 请求参数封装等领域。

🔧 建议改进点：
- 修复 `__expr__` → `__repr__`
- 添加 `__contains__`, `__len__` 支持
- 提供 from_dict() 类方法
- 支持冻结模式（防止修改）

---
> 文档版本：v1.0  
> 最后更新：2025-04-05
```