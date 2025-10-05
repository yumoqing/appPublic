# FiniteStateMachine.py 技术文档

本文档描述了 `FiniteStateMachine.py` 模块的设计与使用方式，该模块实现了一个轻量级的有限状态机（Finite State Machine, FSM）系统，适用于需要状态驱动行为的对象管理。

---

## 1. 概述

本模块提供了一套基于类的有限状态机框架，包含以下核心组件：

- `BaseFSM`: 所有具体状态类的抽象基类。
- `FSMManager`: 状态管理器，用于注册和调度不同状态的行为逻辑。
- `FSMObject`: 支持状态切换的游戏或业务对象基类。

该设计采用**状态模式**（State Pattern），将状态的行为封装在独立的状态对象中，并通过管理器统一调度。

---

## 2. 核心类说明

### 2.1 `BaseFSM` —— 状态行为抽象基类

`BaseFSM` 是所有具体状态类必须继承的抽象基类。它定义了状态的三个生命周期方法。

#### 方法接口

| 方法 | 描述 |
|------|------|
| `enterState(obj)` | 当对象进入此状态时调用。通常用于初始化操作。 |
| `execState(obj)`  | 在每帧或每次更新周期中执行当前状态的逻辑。 |
| `exitState(obj)`  | 当对象退出此状态前调用。可用于清理资源或保存状态数据。 |

> ⚠️ 注意：这三个方法均为抽象方法，子类必须重写，否则会抛出 `NotImplementedError`。

#### 示例子类定义（用户需自行实现）

```python
class IdleState(BaseFSM):
    def enterState(self, obj):
        print(f"{obj} 进入空闲状态")

    def execState(self, obj):
        print(f"{obj} 正处于空闲状态")

    def exitState(self, obj):
        print(f"{obj} 离开空闲状态")
```

---

### 2.2 `FSMManager` —— 有限状态机管理器

全局唯一的状态管理器，负责维护状态与其对应 FSM 实例之间的映射关系，并驱动状态更新流程。

#### 属性

- `_fsms` (`dict`)：内部字典，键为状态标识（如字符串），值为对应的 `BaseFSM` 子类实例。

#### 构造函数

```python
def __init__(self)
```

初始化一个空的状态映射表。

#### 公共方法

| 方法 | 参数 | 返回值 | 描述 |
|------|------|--------|------|
| `addState(state, fsm)` | `state`: str 或 hashable<br>`fsm`: BaseFSM 实例 | 无 | 将指定状态名绑定到一个 FSM 实例上。 |
| `delState(state)` | `state`: 要删除的状态名 | 无 | 移除指定状态及其 FSM 实例。若状态不存在则引发 KeyError。 |
| `getFSM(state)` | `state`: 查询的状态名 | BaseFSM 实例 | 获取与状态名关联的 FSM 对象。若未注册则引发 KeyError。 |
| `frame(objs, state)` | `objs`: 可迭代的 FSMObject 列表<br>`state`: 当前期望状态 | 无 | 遍历对象列表，根据其当前状态决定是否切换或保持状态。 |

#### `frame()` 方法逻辑详解

```python
def frame(self, objs, state):
    for obj in objs:
        if state == obj.curr_state:
            obj.keepState()
        else:
            obj.changeState(state, self._fsms[state])
```

- 若对象当前状态等于目标状态 → 调用 `keepState()` 继续执行当前状态逻辑。
- 否则 → 调用 `changeState()` 切换至新状态，并加载对应 FSM 行为。

> ✅ 推荐用法：每一游戏/逻辑帧调用一次 `manager.frame(objects, current_global_state)` 来同步所有对象的状态行为。

---

### 2.3 `FSMObject` —— 支持状态机的对象基类

表示可以拥有有限状态机行为的实体对象（例如游戏角色、UI 控件等）。

#### 属性

| 属性 | 类型 | 描述 |
|------|------|------|
| `fsm_cur_state` | hashable (e.g., str) | 当前所处的状态标识。 |
| `fsm_state_object` | BaseFSM 实例 | 当前状态对应的行为控制器。 |

#### 方法

| 方法 | 参数 | 返回值 | 描述 |
|------|------|--------|------|
| `attachFSM(state, fsm)` | `state`: 初始状态名<br>`fsm`: BaseFSM 实例 | 无 | 初始化对象的状态机，设置初始状态及行为逻辑。 |
| `changeState(new_state, newfsm)` | `new_state`: 新状态名<br>`newfsm`: 新状态对应的 FSM 实例 | 无 | 执行完整的状态切换流程：<br>1. 调用旧状态的 `exitState`<br>2. 更新状态和 FSM 实例<br>3. 调用新状态的 `enterState` 和 `execState` |
| `keepState()` | 无 | 无 | 维持当前状态，仅执行当前 FSM 的 `execState(self)` 方法。 |

> 🔁 **注意**：`changeState` 中存在变量名拼写错误：`new_fsm` 应为 `newfsm`（见下文“已知问题”）。

---

## 3. 使用示例

```python
# 定义两个状态
class WalkingState(BaseFSM):
    def enterState(self, obj):
        print("开始行走")

    def execState(self, obj):
        print("正在行走...")

    def exitState(self, obj):
        print("停止行走")

class JumpingState(BaseFSM):
    def enterState(self, obj):
        print("起跳！")

    def execState(self, obj):
        print("空中飞行...")

    def exitState(self, obj):
        print("落地")

# 创建管理器并注册状态
manager = FSMManager()
manager.addState("walk", WalkingState())
manager.addState("jump", JumpingState())

# 创建对象并附加初始状态
player = FSMObject()
player.attachFSM("walk", WalkingState())

# 模拟运行帧
objects = [player]
manager.frame(objects, "jump")  # 切换到跳跃状态
manager.frame(objects, "jump")  # 保持跳跃状态
manager.frame(objects, "walk")  # 切回行走状态
```

**输出结果：**
```
开始行走
正在行走...
起跳！
空中飞行...
落地
开始行走
正在行走...
```

---

## 4. 已知问题与改进建议

### ❌ Bug: 变量名拼写错误

在 `FSMObject.changeState()` 方法中：

```python
self.fsm_state_object = new_fsm  # 错误：应为 newfsm
```

✅ 正确写法应为：
```python
self.fsm_state_object = newfsm
```

建议修复如下：

```python
def changeState(self, new_state, newfsm):
    self.fsm_state_object.exitState(self)
    self.fsm_cur_state = new_state
    self.fsm_state_object = newfsm
    self.fsm_state_object.enterState(self)
    self.fsm_state_object.execState(self)
```

### 🛠 建议改进

| 改进点 | 说明 |
|-------|------|
| 添加异常处理 | 在 `getFSM()` 和 `delState()` 中加入 `KeyError` 捕获并友好提示。 |
| 支持状态栈（Push/Pop） | 可扩展支持暂停当前状态、临时进入另一个状态后再返回。 |
| 引入状态转换条件 | 当前由外部控制切换，可引入 `canEnter()` 方法判断是否允许进入某状态。 |
| 使用枚举作为状态类型 | 提高类型安全性，避免字符串硬编码错误。 |

---

## 5. 总结

`FiniteStateMachine.py` 提供了一个简洁、可扩展的状态机基础架构，适合用于：

- 游戏开发中的角色行为控制
- UI 状态流转管理
- 机器人动作序列控制
- 任何需要清晰状态划分的系统

通过组合 `BaseFSM` 子类、`FSMManager` 和 `FSMObject`，开发者可以轻松构建模块化、易维护的状态驱动程序。

--- 

📌 **版本信息**  
- 文件名: `FiniteStateMachine.py`
- 设计模式: 状态模式（State Pattern）
- 适用范围: Python 3.x