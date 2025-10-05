# `TimeCost` 性能计时工具技术文档

---

## 概述

`TimeCost` 是一个基于上下文管理器（Context Manager）的轻量级 Python 性能分析工具，用于记录代码块的执行时间。它通过装饰器模式和全局字典 `timerecord` 累积多个调用的时间开销，便于后续统计与分析。

该模块适用于开发调试、性能优化等场景，支持按名称分类记录耗时，并提供清除和展示功能。

> **注意**：此模块依赖于标准库 `time` 和 `datetime`，并使用了自定义的单例装饰器 `SingletonDecorator`（当前未使用，但已导入）。

---

## 模块依赖

```python
import time
import datetime
from .Singleton import SingletonDecorator
```

- `time`: 用于获取高精度时间戳。
- `datetime`: 当前未实际使用，可考虑移除以减少冗余。
- `SingletonDecorator`: 导入但未在类中应用，可能为预留扩展功能。

---

## 全局变量

```python
timerecord = {}
```

- 类型：字典（`dict`）
- 键（key）：字符串，表示计时任务的名称。
- 值（value）：浮点数列表，存储每次该任务的执行耗时（单位：秒）。

示例：
```python
{
    "database_query": [0.12, 0.15, 0.11],
    "file_load": [0.45, 0.38]
}
```

---

## 核心类：`TimeCost`

### 类定义

```python
class TimeCost:
    def __init__(self, name):
        self.name = name
```

- **作用**：初始化一个以 `name` 命名的计时器。
- **参数**：
  - `name` (str): 计时任务的标识名称，用于区分不同的代码段。

---

### 上下文管理器方法

#### `__enter__`

```python
def __enter__(self):
    self.begin_time = time.time()
```

- 在进入 `with` 语句块时自动调用。
- 记录当前时间作为起始时间戳（`begin_time`），单位为秒（float）。

#### `__exit__`

```python
def __exit__(self, *args):
    self.end_time = time.time()
    d = timerecord.get(self.name, [])
    d.append(self.end_time - self.begin_time)
    timerecord[self.name] = d
```

- 在退出 `with` 语句块时自动调用。
- 计算耗时（`end_time - begin_time`），并将结果追加到对应名称的计时列表中。
- 若该名称首次出现，则创建新列表。

---

### 方法说明

#### `clear(self)`

```python
def clear(self):
    timerecord = {}
```

> ⚠️ **注意：此方法存在严重缺陷**

- 此处的 `timerecord = {}` 仅在局部作用域内重新绑定变量，**不会修改外部全局字典**。
- 实际上 **无任何效果**。

✅ **建议修复方案**：
```python
def clear(self):
    timerecord.clear()  # 清空全局字典内容
```

---

#### `@classmethod clear_all(cls)`

```python
@classmethod
def clear_all(cls):
    timerecord = {}
```

> ⚠️ 同样存在问题：局部赋值无法影响全局 `timerecord`

✅ **正确实现应为**：
```python
@classmethod
def clear_all(cls):
    timerecord.clear()
```

或：

```python
@classmethod
def clear_all(cls):
    global timerecord
    timerecord = {}
```

---

#### `@classmethod clear(cls, name)`

```python
@classmethod
def clear(cls, name):
    timerecord[name] = []
```

- 清除指定名称的所有历史耗时记录。
- 如果 `name` 不存在，会自动创建一个空列表。
- ✅ 此方法是线程不安全的，但在单线程环境下可用。

---

#### `@classmethod show(cls)`

```python
@classmethod
def show(cls):
    def getTimeCost(name):
        x = timerecord.get(name, [])
        if len(x) == 0:
            return 0, 0, 0
        return len(x), sum(x), sum(x)/len(x)

    print('TimeCost ....')
    for name in timerecord.keys():
        print(name, *getTimeCost(name))
```

- 打印所有已记录任务的统计信息。
- 输出格式：`<name> <调用次数> <总耗时> <平均耗时>`
- 示例输出：
  ```
  TimeCost ....
  database_query 3 0.38 0.127
  file_load 2 0.83 0.415
  ```

##### 子函数 `getTimeCost(name)`
- 返回三元组：`(调用次数, 总耗时, 平均耗时)`
- 若无记录，则返回 `(0, 0, 0)`

---

## 使用示例

### 基本用法

```python
from your_module import TimeCost

# 测量某段代码的执行时间
with TimeCost("test_function"):
    time.sleep(1)

with TimeCost("test_function"):
    time.sleep(0.5)

# 显示统计结果
TimeCost.show()
```

**输出示例**：
```
TimeCost ....
test_function 2 1.5 0.75
```

### 清除记录

```python
# 清除特定任务记录
TimeCost.clear("test_function")

# 或清除全部（需修复后才有效）
TimeCost.clear_all()
```

---

## 已知问题与改进建议

| 问题 | 描述 | 建议 |
|------|------|-------|
| `clear()` 方法无效 | 局部变量赋值无法修改全局状态 | 改用 `timerecord.clear()` 或 `global` 关键字 |
| `clear_all()` 方法无效 | 同上 | 同上 |
| `datetime` 未使用 | 冗余导入 | 可移除 |
| 非线程安全 | 多线程下可能产生竞争条件 | 如需并发支持，应加锁机制 |
| 缺少持久化/导出功能 | 仅支持打印 | 可增加 `.to_dict()` 或 `.export_json()` 方法 |

---

## 安全性与注意事项

- 该类不是线程安全的。多线程环境中使用可能导致数据错乱。
- 所有计时数据保存在内存中，程序重启后丢失。
- 名称冲突会导致数据合并，请确保不同逻辑使用唯一 `name`。

---

## 总结

`TimeCost` 提供了一种简洁优雅的方式对代码块进行性能采样，适合快速定位性能瓶颈。尽管目前存在一些作用域相关的 bug，但结构清晰、易于理解和扩展。

经适当修复后，可作为项目中的轻量级性能监控组件。

---

📌 **推荐修复后的完整类片段（关键部分）**：

```python
@classmethod
def clear_all(cls):
    timerecord.clear()  # 或使用 global timerecord; timerecord = {}

def clear(self):
    timerecord.clear()

@classmethod
def clear(cls, name):
    timerecord[name] = []
```