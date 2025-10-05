# ObjectCache 技术文档

```markdown
# ObjectCache 类技术文档

## 概述

`ObjectCache` 是一个基于字典的内存对象缓存类，用于管理具有大小属性的对象集合。它继承自 Python 内置的 `dict` 类，并扩展了容量限制、自动淘汰和访问时间追踪功能。

该缓存适用于需要控制内存使用量、并能通过 `.get_size()` 方法获取对象大小的场景。当缓存总大小接近预设上限时，会触发基于最近最少使用（LRU）策略的半数淘汰机制。

---

## 特性

- 支持类似字典的键值存储操作。
- 自动跟踪每个对象的大小（需实现 `get_size()` 方法）。
- 设置最大缓存容量（以字节或其他单位计），防止内存溢出。
- 使用 LRU（最近最少使用）策略进行对象淘汰。
- 记录对象最后访问时间以支持淘汰逻辑。

---

## 类定义

```python
class ObjectCache(dict)
```

继承自 `dict`，因此支持所有标准字典操作（如 `in`, `len()`, 迭代等）。

---

## 初始化方法

### `__init__(self, maxsize=10000000, *args)`

#### 参数说明：

| 参数      | 类型   | 说明 |
|-----------|--------|------|
| `maxsize` | int    | 缓存允许的最大总大小，默认为 10,000,000 单位（例如字节）。 |
| `*args`   | tuple  | 传递给父类 `dict` 的初始化参数（可选）。 |

#### 属性初始化：

| 属性       | 类型   | 说明 |
|------------|--------|------|
| `self.maxsize` | int  | 最大缓存容量限制。 |
| `self.size`    | int  | 当前缓存中所有对象的总大小，初始为 0。 |
| `self._shadow` | dict | 私有字典，记录每个键对应的 `[最后访问时间, 对象大小]`。 |

> ⚠️ 注意：必须导入 `time` 模块，否则在设置项时会抛出 `NameError`。

---

## 核心方法

### `__setitem__(key, item)`

将对象插入或更新到缓存中。

#### 行为流程：

1. 调用 `item.get_size()` 获取对象大小。
2. 若失败（无此方法或异常），则直接返回，不缓存该对象。
3. 成功获取大小后，将其加到 `self.size`。
4. 如果当前总大小超过 `maxsize`：
   - 从 `self._shadow` 中提取所有 `(访问时间, key)` 元组。
   - 按访问时间排序（越早访问的排在前面）。
   - 删除前一半最久未访问的条目及其对应的数据。
5. 调用父类 `__setitem__` 存储新对象。
6. 在 `_shadow` 中记录其访问时间和大小。

#### 注意事项：

- 存在 bug：`tmp[i][i]` 应为 `tmp[i][1]`（即 key），原代码会导致索引错误。
- 正确写法应为：
  ```python
  for i in xrange(len(tmp)//2):
      del self[tmp[i][1]]  # tmp[i] 是 (time, key)，所以取 [1]
  ```

---

### `__getitem__(key)`

获取指定键对应的对象。

#### 行为流程：

1. 尝试调用父类 `__getitem__` 获取对象。
2. 若存在，则更新该键在 `_shadow` 中的访问时间为当前时间（`time.time()`）。
3. 返回对象。

#### 异常处理：

- 若键不存在，重新抛出 `KeyError`。

---

### `get(key, default=None)`

安全获取指定键的对象，若不存在返回默认值。

#### 参数：

| 参数     | 类型 | 说明 |
|----------|------|------|
| `key`     | any  | 要查找的键。 |
| `default` | any  | 键不存在时返回的默认值，默认为 `None`。 |

#### 实现逻辑：

- 调用 `self.has_key(key)` 判断是否存在。
- 存在则返回 `self[key]`（触发 `__getitem__` 并更新时间戳）。
- 否则返回 `default`。

> ✅ 推荐使用方式：比直接捕获异常更安全。

---

### `__delitem__(key)`

删除指定键的对象。

#### 行为流程：

1. 调用父类 `__delitem__` 删除主缓存中的对象。
2. 若成功，从 `self.size` 中减去该对象的大小。
3. 从 `self._shadow` 中删除对应的元数据。

#### 异常处理：

- 删除失败时重新抛出异常。

---

## 使用示例

```python
import time

class MyData:
    def __init__(self, data):
        self.data = data

    def get_size(self):
        return len(self.data)

# 创建缓存实例，最大容量为 1MB
cache = ObjectCache(maxsize=1024*1024)

# 添加对象
obj = MyData("Hello World" * 100)
cache['key1'] = obj

# 获取对象
data = cache.get('key1')
print(data)

# 删除对象
del cache['key1']
```

---

## 已知问题与改进建议

### ❌ Bug 修复建议

在 `__setitem__` 方法中：

```python
for i in xrange(len(tmp)//2) :
    del self[tmp[i][i]]
```

应改为：

```python
for _, key in tmp[:len(tmp)//2]:
    del self[key]
```

或者修正索引错误：

```python
for i in range(len(tmp)//2):
    del self[tmp[i][1]]  # 取出 key
```

此外，Python 2 风格的 `xrange` 和 `.iteritems()` 建议升级为 Python 3 兼容语法。

---

### ⚙️ 性能优化建议

- 当前淘汰策略每次都要排序全部元素，复杂度为 O(n log n)，效率较低。
- 可替换为优先队列或双向链表实现真正的 LRU 缓存，提升性能。
- `_shadow` 结构可以考虑合并进主字典，减少维护成本。

---

### 💡 扩展功能建议

- 提供 `clear()` 方法重写以同步清理 `_shadow` 和 `size`。
- 添加 `__contains__`、`keys()` 等方法的行为说明。
- 增加线程安全锁（多线程环境下使用时）。

---

## 依赖要求

- Python 2.7 或兼容版本（当前代码为 Python 2 风格）
- 必须导入模块：
  ```python
  import time
  ```
  否则运行时报错。

---

## 总结

`ObjectCache` 是一个轻量级的对象缓存工具，适合对内存敏感的应用场景。尽管存在一些实现缺陷，但其设计思路清晰，易于理解和扩展。建议在生产环境中结合更成熟的缓存库（如 `functools.lru_cache` 或第三方库 `cachetools`）使用，或在此基础上修复 bug 后封装成稳定组件。
```