# 事件绑定与属性监听技术文档

## 概述

本文档介绍一个基于 `EventDispatcher` 的事件系统扩展，通过 `EventProperty` 类实现可观察的类属性。当属性值发生变化时，会自动触发对应的事件，并通知所有注册的监听器。

该模块结合了事件分发机制和 Python 描述符协议，实现了简洁、灵活的状态变化响应模式，适用于 GUI 编程、状态管理、MVVM 架构等场景。

---

## 依赖模块

- `eventpy.eventdispatcher.EventDispatcher`：基础事件分发类。
- `appPublic.dictObject.DictObject`：用于封装事件数据的对象，支持点语法访问属性。

---

## 扩展方法：`bind` 和 `unbind`

为了简化事件监听器的注册与移除操作，为 `EventDispatcher` 类动态添加了两个便捷方法：

### `bind(self, eventname, handler)`
将指定处理器绑定到某个事件名上。

| 参数       | 类型     | 说明                     |
|------------|----------|--------------------------|
| `self`     | object   | EventDispatcher 实例     |
| `eventname`| str      | 事件名称（字符串标识）   |
| `handler`  | callable | 事件触发时调用的函数或方法 |

> 等价于调用 `appendListener(eventname, handler)`

### `unbind(self, eventname, handler)`
从指定事件中移除处理器。

| 参数       | 类型     | 说明                     |
|------------|----------|--------------------------|
| `self`     | object   | EventDispatcher 实例     |
| `eventname`| str      | 事件名称                 |
| `handler`  | callable | 要移除的处理器函数       |

> 等价于调用 `removeListener(eventname, handler)`

::: warning 注意
在当前实现中，`unbind` 方法可能存在未正确移除监听器的问题（见主程序注释），需确保 `EventDispatcher` 原生的 `removeListener` 方法功能正常。
:::

```python
EventDispatcher.bind = bind
EventDispatcher.unbind = unbind
```

---

## 核心类：`EventProperty`

`EventProperty` 是一个描述符类，用于定义能够触发事件的类级属性。

### 初始化

```python
def __init__(self, event_name, initial_value=None)
```

| 参数            | 类型  | 说明                                   |
|------------------|-------|----------------------------------------|
| `event_name`     | str   | 属性变更时触发的事件名称               |
| `initial_value`  | any   | 属性的初始值（默认为 `None`）          |

### 描述符行为

#### `__get__(self, instance, owner)`
返回属性当前值。

- 若通过类访问（`instance` 为 `None`），返回描述符实例本身。
- 若通过实例访问，返回内部存储的 `_value`。

#### `__set__(self, instance, value)`
设置新值并触发事件（仅当值发生改变时）。

1. 比较新旧值，若相同则不执行任何操作。
2. 更新内部 `_value`。
3. 创建一个 `DictObject` 实例封装事件数据：
   - `.target`: 触发事件的实例对象
   - `.data`: 新值
   - `.event`: 事件名称
4. 调用 `instance.dispatch(event_name, data)` 分发事件。

---

## 使用示例

以下代码演示如何使用 `EventProperty` 和事件绑定机制：

```python
class SomeClass(EventDispatcher):
    state = EventProperty('onstate', 0)   # 初始值为 0，变化时触发 'onstate'
    age = EventProperty('onage', 20)      # 初始值为 20，变化时触发 'onage'

    def __init__(self):
        super().__init__()  # 初始化父类事件系统
```

### 定义监听器

```python
def observer1(data):
    print(f"Observer 1 received: {data}")

def observer2(data):
    print(f"Observer 2 received: {data}")

def observer3(data):
    print(f"Observer 3 received: {data}")
```

每个监听器接收一个 `data` 参数，其类型为 `DictObject`，包含：

- `data.target`: 发生变化的实例
- `data.data`: 新的属性值
- `data.event`: 事件名称（如 `'onstate'`）

### 绑定事件监听

```python
si = SomeClass()
si.bind('onstate', observer1)
si.bind('onstate', observer2)
si.bind('onage', observer3)
```

### 属性赋值触发事件

```python
si.state = 10
# 输出:
# Observer 1 received: <DictObject target=... data=10 event='onstate'>
# Observer 2 received: <DictObject target=... data=10 event='onstate'>

si.state = 20
# 输出:
# Observer 1 received: ...
# Observer 2 received: ...

si.age = 30
# 输出:
# Observer 3 received: <DictObject target=... data=30 event='onage'>
```

每次修改 `state` 或 `age`，只要值不同，就会广播对应事件。

---

## 注意事项与限制

1. **单例值共享问题**  
   多个实例共享同一个 `EventProperty` 描述符中的 `_value`？  
   ❌ 实现中存在潜在 bug：`_value` 是描述符实例变量，如果多个实例共用同一描述符，则可能造成状态污染。  
   ✅ 正确做法应将值存储在实例字典中（例如使用 `instance.__dict__` 或弱引用映射）。当前实现是**非实例安全的**！

   > ⚠️ 当前实现中，所有实例共享 `_value`，这是严重缺陷！建议改进如下：

   ```python
   def __set__(self, instance, value):
       if getattr(instance, f"_{self.event_name}_value") != value:
           setattr(instance, f"_{self.event_name}_value", value)
           # ... dispatch event
   ```

2. **`unbind` 可能无效**
   示例中注释指出 `unbind` 存在错误，可能是 `removeListener` 实现问题或函数引用不一致导致无法匹配。

3. **事件数据结构**
   推荐统一规范 `DictObject` 的字段命名，便于前端或其他模块解析。

---

## 改进建议

| 项目 | 建议 |
|------|------|
| 状态隔离 | 将 `_value` 存储在实例上而非描述符中，避免跨实例污染 |
| 类型提示 | 添加类型注解提升可维护性 |
| 文档字符串 | 为类和方法补充 docstring |
| 单元测试 | 添加测试用例验证绑定、解绑、事件触发逻辑 |

---

## 总结

本模块通过组合 `EventDispatcher` 和描述符机制，提供了一种声明式的方式来实现属性变化监听。尽管当前实现存在一些设计缺陷（特别是状态共享问题），但整体架构清晰，易于扩展。

适用于需要轻量级响应式编程能力的 Python 应用，经过适当优化后可用于生产环境。

--- 

> ✅ 提示：建议重构 `EventProperty` 以支持实例级状态存储，确保线程安全和多实例兼容性。