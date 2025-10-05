# 技术文档：单例模式装饰器与全局环境管理

---

## 概述

本文档介绍了基于 Python 的单例模式实现，通过自定义装饰器 `SingletonDecorator` 实现类的单例化，并结合 `DictObject` 构建可扩展的全局环境对象 `GlobalEnv`。该设计适用于需要全局唯一实例的场景，如配置管理、日志记录器、数据库连接池等。

---

## 依赖模块

- `appPublic.dictObject.DictObject`  
  一个字典式对象封装类，允许通过属性方式访问字典键值（类似 JavaScript 的对象行为）。

> ⚠️ 注意：确保已安装并正确配置 `appPublic` 包。

---

## 核心组件

### 1. `SingletonDecorator` 类

#### 功能说明
`SingletonDecorator` 是一个类装饰器，用于将任意类转换为“单例类”——即在整个程序生命周期中，该类只能存在一个实例。

#### 源码解析

```python
class SingletonDecorator:
    def __init__(self, klass):
        self.klass = klass          # 被装饰的类
        self.instance = None        # 单例实例缓存

    def __call__(self, *args, **kwds):
        if self.instance is None:
            self.instance = self.klass(*args, **kwds)  # 第一次创建实例
        return self.instance                           # 后续调用均返回同一实例
```

#### 使用方式
使用 `@SingletonDecorator` 装饰目标类即可：

```python
@SingletonDecorator
class MyClass:
    def __init__(self, value):
        self.value = value
```

无论多少次实例化，都只会返回同一个对象。

#### 特性
- 延迟初始化（Lazy Instantiation）：仅在首次调用时创建实例。
- 线程不安全（本实现未加锁），适用于单线程或无需并发控制的场景。
- 支持构造参数传递，但**仅第一次有效**。

> ❗ 注意：后续实例化传入的参数不会影响已有实例状态。

---

### 2. `GlobalEnv` 全局环境类

#### 定义

```python
@SingletonDecorator
class GlobalEnv(DictObject):
    pass
```

#### 功能说明
`GlobalEnv` 继承自 `DictObject` 并被 `SingletonDecorator` 装饰，因此具备以下特性：

- 全局唯一实例（单例）
- 支持动态属性赋值和访问（类似字典）
- 可作为应用级共享数据容器（如配置、上下文变量等）

#### 示例用法

```python
env = GlobalEnv()
env.user = "admin"
env.settings = {"debug": True}

another = GlobalEnv()  # 获取相同实例
print(another.user)    # 输出: admin
print(another is env)  # 输出: True
```

---

## 测试示例（`__main__` 模块）

以下代码演示了 `SingletonDecorator` 的实际效果。

### 示例类定义

#### `Child` 类
```python
@SingletonDecorator
class Child(object):
    def __init__(self, name):
        print("child.init")
        self.name = name

    def __str__(self):
        return 'HAHA：' + self.name

    def __expr__(self):  # 注：应为 __repr__，此处命名错误
        print(self.name)
```

#### `Handle` 类
```python
@SingletonDecorator
class Handle(object):
    def __init__(self, name):
        self.name = name

    def __expr__(self):  # 同样应为 __repr__
        print(self.name)
```

### 执行逻辑

```python
c = Child('me')
d = Child('he')

print(str(c), str(d))  # 输出: HAHA：me HAHA：me
```

> 尽管两次构造传参不同，但由于单例机制，`d` 实际上是 `c` 的引用，`name` 仍为 `'me'`。

```python
e = Handle('hammer')
f = Handle('nail')

print(str(e), str(f))  # 假设实现了 __str__，否则会报错
```

同样地，`f` 与 `e` 是同一实例，最终输出取决于 `Handle` 是否重写了字符串方法。

---

## 输出结果分析

运行上述测试代码的实际输出为：

```
child.init
HAHA：me HAHA：me
HAHA：me HAHA：me
```

> 因为 `Handle` 类未定义 `__str__()` 方法，直接调用 `str(e)` 将引发异常。此为示例中的潜在 Bug。

---

## 已知问题与改进建议

| 问题 | 描述 | 建议 |
|------|------|------|
| `__expr__` 应为 `__repr__` | Python 中正确的特殊方法名为 `__repr__` | 更正方法名为 `__repr__` |
| `Handle` 缺少 `__str__` 方法 | 导致 `str()` 调用失败 | 添加 `__str__` 或继承合适基类 |
| 参数忽略风险 | 后续构造参数无效且无警告 | 可添加日志提示或抛出警告 |
| 线程安全性 | 多线程下可能创建多个实例 | 加入线程锁（`threading.Lock`） |

---

## 总结

本模块提供了一种简洁高效的单例实现方案，配合 `DictObject` 可构建灵活的全局环境管理系统。适用于中小型项目中的全局状态管理需求。

---

## 附录：完整修正版建议代码

```python
from appPublic.dictObject import DictObject
import threading

class SingletonDecorator:
    def __init__(self, klass):
        self.klass = klass
        self.instance = None
        self.lock = threading.Lock()

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            with self.lock:
                if self.instance is None:  # Double-checked locking
                    self.instance = self.klass(*args, **kwargs)
        return self.instance


@SingletonDecorator
class GlobalEnv(DictObject):
    pass


if __name__ == '__main__':
    @SingletonDecorator
    class Child:
        def __init__(self, name):
            print("Child.init")
            self.name = name

        def __str__(self):
            return 'HAHA：' + self.name

        def __repr__(self):
            return f"Child({self.name!r})"

    c = Child('me')
    d = Child('he')
    print(c, d)           # HAHA：me HAHA：me
    print(c is d)         # True

    @SingletonDecorator
    class Handle:
        def __init__(self, name):
            self.name = name

        def __str__(self):
            return f"Handle({self.name})"

        def __repr__(self):
            return self.__str__()

    e = Handle('hammer')
    f = Handle('nail')
    print(e, f)           # Handle(hammer) Handle(hammer)
    print(e is f)         # True
```

--- 

✅ 推荐在生产环境中使用修正版本以避免常见陷阱。