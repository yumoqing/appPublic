# `ObjectAction` 类技术文档

## 概述

`ObjectAction` 是一个基于单例模式设计的通用对象行为管理类，用于注册、管理和执行与特定 `id` 和 `动作（action）` 相关联的函数。它支持精确匹配、通配符匹配（`*`）和默认行为（`#`），适用于事件处理、插件系统或动态行为扩展等场景。

该类通过 `SingletonDecorator` 装饰器确保在整个应用中仅存在一个实例，从而实现全局共享的行为注册表。

---

## 依赖

- `appPublic.Singleton.SingletonDecorator`：提供单例模式支持。

```python
from appPublic.Singleton import SingletonDecorator
```

> 注意：需确保 `appPublic` 包已正确安装并可导入。

---

## 类定义

```python
@SingletonDecorator
class ObjectAction(object):
    pass
```

### 说明
- 使用 `@SingletonDecorator` 确保 `ObjectAction` 为单例类。
- 所有操作均作用于同一个全局实例。

---

## 属性

| 属性名       | 类型   | 描述 |
|--------------|--------|------|
| `actionList` | `dict` | 存储所有注册的行为函数，结构为：<br>`{ id: { action: [func1, func2, ...] } }` |

---

## 方法

### `__init__(self)`

初始化 `actionList` 字典。

#### 示例：
```python
def __init__(self):
    self.actionList = {}
```

---

### `init(self, id, action)`

为指定的 `id` 和 `action` 初始化一个空的函数列表（若尚不存在）。

#### 参数：
| 参数     | 类型   | 说明 |
|----------|--------|------|
| `id`     | `str` 或 `any hashable` | 唯一标识符（如对象ID、类型名等） |
| `action` | `str`                 | 动作名称（如 `'create'`, `'update'` 等） |

#### 行为：
- 如果 `id` 不存在，则创建 `{id: {action: []}}`
- 如果 `action` 已存在，则不覆盖，保持原函数列表

#### 示例：
```python
oa = ObjectAction()
oa.init('user', 'save')  # 创建 user.save 的函数列表
```

---

### `add(self, id, action, func)`

向指定 `id` 和 `action` 注册一个处理函数。

#### 参数：
| 参数     | 类型     | 说明 |
|----------|----------|------|
| `id`     | `str` 或 `any hashable` | 对象标识符 |
| `action` | `str`                 | 动作名称 |
| `func`   | `callable`            | 接受 `(id, action, data)` 并返回 `data` 的函数 |

#### 行为：
- 自动初始化 `id` 和 `action` 对应的结构（如果不存在）
- 将 `func` 添加到对应动作的函数列表末尾（支持多个函数注册）

#### 示例：
```python
def my_handler(id, act, data):
    print(f"Handling {act} for {id}")
    return data + "_handled"

oa = ObjectAction()
oa.add('doc', 'export', my_handler)
```

---

### `execute(self, id, action, data, callback=None)`

执行与 `id` 和 `action` 关联的所有函数，并按优先级顺序处理通配符和默认行为。

#### 参数：
| 参数       | 类型       | 说明 |
|------------|------------|------|
| `id`       | `str` 或 `any hashable` | 要执行操作的对象 ID |
| `action`   | `str`                 | 要触发的动作 |
| `data`     | `any`                | 输入数据（通常会被函数链式处理） |
| `callback` | `callable` 或 `None` | 可选回调函数，在执行完成后调用，接收最终 `data` |

#### 返回值：
- 处理后的 `data`（经过所有函数依次处理）

#### 执行逻辑流程：

1. 若 `action` 为 `'#'` 或 `'*'`，直接返回原始 `data`（避免无限递归或无效调用）
2. 查找 `id` 对应的行为集合 `idA`
3. 获取以下两类函数列表：
   - 精确匹配：`action` 对应的函数列表
   - 通配符匹配：`'*'` 对应的函数列表（适用于所有动作）
4. 先执行上述合并后的函数列表
5. 若无任何函数匹配，则执行默认行为 `'#'` 中的函数
6. 最后调用 `callback(data)`（如有）
7. 返回最终 `data`

#### 函数调用格式：
每个注册函数必须符合签名：
```python
def handler(id, action, data):
    # 处理逻辑
    return modified_data
```

#### 示例：
```python
result = oa.execute('user', 'login', {'status': 'pending'})
```

---

## 特殊动作说明

| 动作符号 | 含义 |
|---------|------|
| `*`     | **通配符动作**：绑定到 `*` 的函数会在**每一个动作执行时都被调用**（除 `#` 和 `*` 自身外） |
| `#`     | **默认动作**：当某个 `id` 没有匹配到具体动作时，执行 `#` 下的函数作为兜底处理 |

> ⚠️ 注意：`action` 为 `*` 或 `#` 时不会触发任何函数（防止循环调用）

---

## 使用示例

```python
# 定义处理函数
def f(id, act, data):
    print(f"f called with {data}")
    return data + "_f"

def f1(id, act, data):
    return data + "_f1"

def f2(id, act, data):
    return data + "_f2"

# 注册函数
def add():
    oa = ObjectAction()
    oa.add('test', 'b', f)      # test.b 触发 f
    oa.add('test', '*', f1)     # 所有 test 的动作都触发 f1
    oa.add('test', '#', f2)     # 默认行为

# 执行动作
def exe():
    oa = ObjectAction()
    result = oa.execute('test', 'a', 'data1')
    print(result)  # 输出: data1_f1_f2 （因为 'a' 不匹配 'b'，但 '*' 和 '#' 生效）

if __name__ == '__main__':
    add()
    exe()
```

---

## 设计特点

| 特性         | 说明 |
|--------------|------|
| ✅ 单例模式   | 全局唯一实例，便于集中管理行为 |
| ✅ 支持通配符 | `*` 实现通用拦截（如日志、权限检查） |
| ✅ 支持默认行为 | `#` 提供 fallback 机制 |
| ✅ 链式处理   | 多个函数可以串联处理同一份数据 |
| ✅ 线程安全？ | ❌ 当前未加锁，多线程环境下需外部同步 |

---

## 注意事项

1. **函数副作用**：每个处理函数应尽量无副作用，且必须返回 `data`（或修改后版本），否则后续函数可能出错。
2. **性能考虑**：频繁调用时建议缓存查找结果，当前每次 `execute` 都进行字典查询。
3. **错误处理**：未内置异常捕获，建议在生产环境中包裹 `try-except`。
4. **不可变数据风险**：若传入不可变对象（如字符串、元组），需确保函数返回新对象。

---

## 测试与调试

模块包含简单测试代码（`if __name__ == '__main__':`），可用于验证基本功能。

```bash
python object_action.py
```

预期输出（根据注释状态不同而变化）：
```
data1_f2
```

（当前示例中 `*` 被注释，只执行了 `#`）

---

## 应用场景

- 插件式业务逻辑扩展
- 事件驱动架构中的处理器注册
- 动态权限/审计钩子
- 数据预处理与后处理管道

---

## 未来优化建议

- 增加 `remove(id, action, func)` 方法以注销函数
- 增加 `clear(id=None)` 清理机制
- 支持优先级排序（如按权重执行）
- 添加日志或调试开关
- 引入线程锁以支持并发环境

---

## 版权与许可

> 本代码由项目团队开发，遵循项目内部开源协议。引用请注明出处。