# `Genetic` 类技术文档

## 概述

`Genetic` 是一个用于实现**属性遗传机制**的基类，支持对象之间的父子关系建立，并允许子对象继承父对象的属性。该设计模拟了一种类似原型继承的机制，适用于需要层级化属性共享与继承的场景。

通过 `__parent__` 和 `__children__` 两个特殊属性维护对象间的树状结构，子对象在访问自身不存在的属性时，会自动向上追溯其父对象，直到根节点。

---

## 类定义

```python
class Genetic:
    """
    A Base class for genetical objects,
    all the instances can inherit attributes from its parent.
    """
```

### 功能特点

- 支持动态属性继承（从父对象获取未定义的属性）
- 维护双向父子关系（父 → 子 和 子 → 父）
- 可构建多层对象继承树
- 易于扩展：其他类可继承 `Genetic` 获得遗传能力

---

## 属性说明

| 属性名         | 类型       | 描述 |
|----------------|------------|------|
| `__parent__`   | `Genetic` 或 `None` | 当前对象的父对象。初始为 `None`。 |
| `__children__` | `List[Genetic]`     | 当前对象的所有子对象列表。初始为空列表。 |

> ⚠️ 注意：这两个属性是私有属性（双下划线命名），不应直接修改，应通过提供的方法管理。

---

## 方法说明

### `__init__(self)`

初始化一个新的 `Genetic` 实例。

#### 行为：
- 设置 `self.__parent__ = None`
- 初始化 `self.__children__ = []`

#### 示例：
```python
obj = Genetic()
print(obj.__parent__)   # 输出: None
print(obj.__children__) # 输出: []
```

---

### `__getattr__(self, name)`

重写 Python 的属性访问机制。当尝试访问对象中不存在的属性时触发。

#### 参数：
- `name` (`str`)：要访问的属性名

#### 返回值：
- 父对象中的对应属性值（递归查找）

#### 异常：
- 若父链终止且仍未找到属性，则抛出 `AttributeError`

#### 查找逻辑：
1. 首先检查当前对象的 `__dict__` 是否包含该属性
2. 若无，且存在父对象，则递归调用 `getattr(parent, name)`
3. 若无父对象仍找不到，抛出 `AttributeError`

> ✅ 提示：此机制实现了“属性冒泡”式继承。

#### 示例：
```python
parent = Genetic()
parent.x = 100

child = Genetic()
child.setParent(parent)

print(child.x)  # 输出: 100（从父继承）
```

---

### `addChild(self, child)`

将指定对象添加为当前对象的一个子对象，并设置其父引用。

#### 参数：
- `child` (`Genetic`)：要添加的子对象实例

#### 行为：
- 将 `child` 添加到 `self.__children__` 列表
- 设置 `child.__parent__ = self`

#### 注意事项：
- 不检查重复或类型，调用者需确保传入有效的 `Genetic` 子类实例
- 建立的是双向链接

---

### `setParent(self, parent)`

设置当前对象的父对象，等价于让父对象执行 `addChild(self)`。

#### 参数：
- `parent` (`Genetic`)：希望设定为父的对象

#### 行为：
- 调用 `parent.addChild(self)`
- 自动完成父子关系绑定

#### 示例：
```python
p = Genetic()
c = Genetic()
c.setParent(p)  # c 成为 p 的子对象
```

---

## 使用示例

以下是一个完整示例，展示如何使用 `Genetic` 构建四层对象树并进行属性继承：

```python
if __name__ == '__main__':
    class A(Genetic):
        def __init__(self, a1, a2):
            Genetic.__init__(self)
            self.a1 = a1
            self.a2 = a2
        
    class B(Genetic):
        def __init__(self, b):
            Genetic.__init__(self)
            self.b = b

    # 创建对象
    gp = A(1, 2)    # 祖先
    p = B(3)        # 父
    c = A(4, 5)     # 子
    gc = B(6)       # 孙子

    # 建立遗传链：gp → p → c → gc
    gc.setParent(c)
    c.setParent(p)
    p.setParent(gp)

    # 测试属性继承
    print(gc.a1)  # 输出: 1 （从 gp 继承）
    print(gc.b)   # 输出: 3 （从 p 继承）
    print(c.a2)   # 输出: 2 （从 gp 继承）
```

### 结构图解

```
gp (A: a1=1, a2=2)
 └── p (B: b=3)
     └── c (A: a1=4, a2=5)
         └── gc (B: b=6)
```

尽管 `gc` 自身没有定义 `a1`，但由于继承链的存在，它可以通过 `__getattr__` 向上查找直至 `gp` 获取 `a1=1`。

---

## 设计原理与适用场景

### 核心思想

- **原型式继承**：类似于 JavaScript 的原型链，对象可以直接从另一个对象继承属性。
- **运行时动态继承**：继承关系在实例化后仍可更改（如更换父对象）。
- **轻量级属性共享**：避免冗余数据复制，适合配置传播、上下文传递等场景。

### 典型应用场景

1. **配置系统**：高层配置向下继承，低层可覆盖
2. **UI 组件树**：样式/主题继承
3. **游戏开发**：角色状态、技能树继承
4. **DSL 或规则引擎**：上下文环境逐层传递

---

## 注意事项与限制

| 项目 | 说明 |
|------|------|
| ❌ 循环引用风险 | 不应形成闭环（如 A→B→A），否则 `__getattr__` 可能导致无限递归 |
| ⚠️ 属性覆盖逻辑 | 当前仅支持“向上查找”，不支持同名属性优先级控制（即无法区分是否显式定义） |
| 📦 私有属性限制 | 双下划线属性（如 `__x`）会被 Python 名称改写，可能导致继承失效 |
| 🔁 多重继承不支持 | 当前模型仅为单亲继承，不处理多个父对象的情况 |

---

## 扩展建议

- 添加 `hasattr_recursive()` 方法判断属性是否可继承
- 实现 `removeChild()` / `clearParent()` 来解除关系
- 增加事件通知机制（如 `on_parent_changed`）
- 支持只读继承或深拷贝模式

---

## 总结

`Genetic` 类提供了一个简洁而强大的对象属性继承框架，利用 Python 的 `__getattr__` 魔法方法和父子引用机制，实现了灵活的运行时属性共享。适合作为基础组件集成进需要层次化数据管理的系统中。

> 💡 “不是所有对象都需要基因，但一旦拥有，传承便有了意义。”