# `ExecFile.py` 技术文档

```markdown
# ExecFile.py - 动态执行 Python 配置文件并构建配置对象

`ExecFile.py` 是一个轻量级的 Python 模块，用于从 `.py` 或 `.ini` 类似格式的文本文件中动态加载配置数据。它通过 `exec()` 执行文件内容，并将变量注入指定命名空间，支持嵌套字典自动转换为可属性访问的对象。

---

## 概述

该模块主要包含两个核心类：

- `DictConfig`: 一个增强型字典类，允许通过属性语法访问键值，并支持嵌套结构递归转换。
- `ExecFile`: 提供运行外部配置文件的能力，可设置变量、执行脚本并获取结果。

典型应用场景包括：
- 加载可编程的配置文件（如卡片配置、游戏规则等）
- 实现插件式配置系统
- 将 Python 脚本作为配置源使用

---

## 安装与导入

无需安装，直接将 `ExecFile.py` 放入项目路径后导入即可：

```python
from ExecFile import ExecFile, DictConfig
```

---

## 核心类说明

### 1. `DictConfig(dic=None, path=None, str=None, namespace={})`

一个支持属性访问和嵌套结构解析的字典类。

#### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `dic` | `dict` | 初始字典数据，会被深度转换为 `DictConfig` 对象 |
| `path` | `str` | 配置文件路径，自动读取并执行其中的 Python 代码 |
| `str` | `str` | 包含 Python 代码的字符串，将在指定命名空间中执行 |
| `namespace` | `dict` | 执行代码时使用的全局命名空间 |

> ⚠️ 注意：`path` 和 `str` 不能同时为 `None`；若提供多个参数，则按顺序依次处理。

#### 属性与方法

##### `.keys()`
返回所有键名。

##### `.__getitem__(key)`
支持 `obj[key]` 访问方式。

##### `.__getattr__(name)`
支持 `obj.name` 属性式访问。如果属性不存在则抛出 `AttributeError`。

##### `.__subConfig()`
私有方法：递归遍历字典中的结构化数据（`dict`, `list`, `tuple`），将其中的 `dict` 自动转为 `DictConfig` 实例，实现链式属性访问。

例如：
```python
data = {'user': {'name': 'Alice', 'age': 30}}
config = DictConfig(dic=data)
print(config.user.name)  # 输出: Alice
```

##### `.__load(path)`
私有方法：从文件路径加载内容并执行，提取变量到当前实例。

---

### 2. `ExecFile(obj=None, path=None, namespace={})`

用于执行外部 Python 风格配置文件的核心类。

#### 参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `obj` | `object` | 目标对象，配置变量将被注入此对象的 `__dict__` 中。默认为 `self` |
| `path` | `str` | 要执行的配置文件路径（可选） |
| `namespace` | `dict` | 全局命名空间（目前未完全启用） |

#### 方法

##### `.set(name, v)`
设置目标对象的一个属性。

**参数：**
- `name` (str): 属性名
- `v`: 属性值

**示例：**
```python
r = ExecFile()
r.set('game_mode', 'hard')
```

##### `.get(name, default=None)`
获取目标对象的属性值，若不存在返回默认值。

**参数：**
- `name` (str): 属性名
- `default`: 默认返回值

**示例：**
```python
mode = r.get('game_mode', 'normal')
```

##### `.run(path=None)`
执行指定路径的配置文件。

**参数：**
- `path` (str): 配置文件路径。若传入则更新内部路径记录。

**返回值：**
- 成功时返回 `(True, '')`
- 失败时返回 `(False, Exception)` 并打印错误信息

**行为说明：**
- 使用 `open()` 读取文件内容
- 通过 `exec(buf, globals(), self.__object.__dict__)` 执行代码，变量注入目标对象
- 若文件路径未设置且未传参，则抛出异常

---

## 使用示例

### 示例 1：基本用法 —— 加载配置文件

假设有一个配置文件 `test/cards.ini` 内容如下：

```python
# test/cards.ini
cards = [
    {'id': 1, 'name': 'Fireball', 'damage': 50},
    {'id': 2, 'name': 'Shield', 'damage': 0}
]
game_version = "1.0.0"
max_players = 4
```

使用 `ExecFile` 加载：

```python
r = ExecFile()
r.run('test/cards.ini')

# 访问配置项
print(r.cards[0]['name'])        # 输出: Fireball
print(r.game_version)            # 输出: 1.0.0
print(r.max_players)             # 输出: 4
```

### 示例 2：预设变量 + 执行文件

```python
r = ExecFile()
r.set('player_level', 5)
r.run('test/cards.ini')

# 在 cards.ini 中可以引用 player_level 变量
# 例如：bonus_damage = player_level * 10
```

### 示例 3：结合 DictConfig 解析嵌套结构

```python
config_str = """
user = {
    'profile': {
        'name': 'Bob',
        'settings': ['dark_mode', 'notifications']
    }
}
"""

dc = DictConfig(str=config_str)
print(dc.user.profile.name)  # 输出: Bob
print(dc.user.profile.settings)  # 输出: ['dark_mode', 'notifications']
```

---

## 文件格式要求

配置文件应为合法的 Python 语法片段，常见形式包括：

- 变量赋值：`var = value`
- 字典定义：`config = {'key': 'value'}`
- 列表/元组：`items = [1, 2, 3]`
- 支持表达式计算（依赖已定义变量）

⚠️ **安全警告**：由于使用了 `exec()`，请确保配置文件来源可信，避免远程或用户上传执行。

---

## 错误处理

- `run()` 方法捕获所有异常并输出错误日志：
  ```
  ExecFile() <Exception Message> <FilePath>
  ```
- 返回 `(False, exception)` 表示执行失败，调用者应进行相应处理。

---

## 已知限制

1. 不支持异步文件读取
2. `__load()` 方法在 `DictConfig` 中存在但未被公开调用接口
3. 命名空间机制较简单，`globals()` 被直接传递
4. 异常处理较为基础，仅打印信息无重试机制

---

## 版本信息

- 创建时间：未知
- 作者：未知
- 语言版本：Python 2/3 兼容（建议 Python 3.x）

> 注：代码中使用了 `print` 函数兼容写法，适用于 Python 3。

---

## 总结

`ExecFile.py` 提供了一种灵活的方式来加载“代码即配置”的 `.py` 或 `.ini` 风格文件，适合小型项目或需要动态逻辑配置的场景。配合 `DictConfig` 可实现优雅的嵌套配置访问。

推荐在受控环境中使用，注意安全风险。

---
```