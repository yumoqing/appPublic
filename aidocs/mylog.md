# MyLog 日志系统技术文档

本文档描述了一个基于 Python 的轻量级日志管理系统 `MyLog` 与 `LogMan`，用于实现灵活的日志记录和分类控制。该系统支持多类别日志输出、动态注册日志处理器，并结合全局数据管理模块 `public_data` 实现单例模式的日志管理。

---

## 目录

- [概述](#概述)
- [依赖模块](#依赖模块)
- [核心常量](#核心常量)
- [类说明](#类说明)
  - [`MyLog`](#mylog)
  - [`LogMan`](#logman)
- [函数说明](#函数说明)
  - [`mylog()`](#mylogs-catelogappinfo)
- [使用示例](#使用示例)
- [注意事项](#注意事项)

---

## 概述

本日志系统提供以下功能：

- 支持按**日志级别/类别**（如 `SYSError`, `APPInfo`, `DEBUG1` 等）进行过滤。
- 可动态添加、删除或修改日志处理器（logger）。
- 使用统一入口函数 `mylog()` 记录消息。
- 日志自动写入文件 `./log/my.log`。
- 基于 `public_data` 全局变量存储日志管理器实例，避免重复初始化。

---

## 依赖模块

| 模块名         | 用途说明 |
|----------------|----------|
| `os`           | 路径拼接、文件操作 |
| `datetime`     | 获取当前时间用于日志时间戳 |
| `PublicData`   | 全局数据容器，保存共享对象（如 `ProgramPath`, `mylog` 实例） |
| `folderUtils.mkdir` | 自动创建目录（确保日志目录存在） |

> ⚠️ 注意：`PublicData` 和 `folderUtils` 是项目自定义模块，需保证其可用性。

---

## 核心常量

```python
AllCatelogs = [
    'SYSError',
    'SYSWarn',
    'APPError',
    'APPWarn',
    'APPInfo',
    'DEBUG1',
    'DEBUG2',
    'DEBUG3',
    'DEBUG4',
    'DEBUG5',
]
```

- **作用**：预定义所有允许的日志类别（日志等级/标签）。
- **说明**：
  - 分为系统级 (`SYS*`) 和应用级 (`APP*`)。
  - `DEBUG1` 到 `DEBUG5` 可用于不同级别的调试信息输出。
  - 所有日志操作必须使用这些类别之一，否则将被忽略。

---

## 类说明

### `MyLog`

一个简单的日志写入类，负责将日志消息追加到指定路径的文件中。

#### 构造函数

```python
def __init__(self, path)
```

- **参数**：
  - `path` (str): 日志根目录路径，默认为 `'.'`（当前目录）

#### 方法

##### `setLogPath(path='.')`

设置日志存储路径，并自动创建 `log` 子目录。

- **参数**：
  - `path` (str): 新的日志根目录路径
- **行为**：
  - 将路径保存至 `self.myLogPath`
  - 创建 `{path}/log/` 目录（若不存在）
- **注意**：此方法存在逻辑错误 —— 缩进问题导致 `logp` 和 `mkdir(logp)` 不在方法体内（见[注意事项](#注意事项)）

##### `__call__(msg='')`

使对象可调用，用于写入一条日志。

- **参数**：
  - `msg` (str): 要写入的消息
- **行为**：
  1. 构造日志文件路径：`{self.myLogPath}/log/my.log`
  2. 以追加模式打开文件
  3. 写入格式化的时间戳 + 消息
  4. 关闭文件
- **时间格式**：`YYYY-MM-DD HH:MM:SS <message>`

> 示例输出：
> ```
> 2025-04-05 10:30:45 User login successful
> ```

---

### `LogMan`（日志管理器）

用于集中管理和分发日志消息到多个日志处理器（logger），支持基于类别的条件触发。

#### 构造函数

```python
def __init__()
```

- 初始化两个属性：
  - `self.logers`: 字典，存储注册的日志处理器
  - `self.catelogs`: 当前允许的日志类别列表（初始为 `AllCatelogs`）

#### 方法

##### `addCatelog(catelog)`

添加新的日志类别到允许列表。

- **参数**：
  - `catelog` (str): 要添加的类别名称
- **行为**：
  - 若类别不在 `self.catelogs` 中，则追加

##### `addLoger(name, func, catelog)`

注册一个新的日志处理器。

- **参数**：
  - `name` (str): 处理器唯一标识名
  - `func` (callable): 可调用对象（如 `MyLog` 实例），用于实际写日志
  - `catelog` (str 或 list of str): 此处理器监听的日志类别
- **行为**：
  - 若 `catelog` 非列表，则转换为列表
  - 过滤掉不在 `self.catelogs` 中的非法类别
  - 构建日志器字典并存入 `self.logers[name]`

##### `delLoger(name)`

删除已注册的日志处理器。

- **参数**：
  - `name` (str): 要删除的日志处理器名称
- **行为**：
  - 若存在则从 `self.logers` 中移除

##### `setCatelog(name, catelog)`

更改某个日志处理器所监听的类别。

- **参数**：
  - `name` (str): 已注册的日志处理器名称
  - `catelog` (str 或 list of str): 新的监听类别
- **行为**：
  - 类别合法性检查与过滤后更新配置

##### `__call__(msg='', catelog='APPInfo')`

使对象可调用，作为日志分发中心。

- **参数**：
  - `msg` (str): 日志内容
  - `catelog` (str): 日志所属类别（默认 `'APPInfo'`）
- **行为**：
  - 遍历所有注册的日志处理器
  - 如果该处理器监听了当前 `catelog`，则调用其 `func(msg)`
- **用途**：实现“发布-订阅”式日志分发机制

---

## 函数说明

### `mylog(s, catelog='APPInfo')`

全局日志接口函数，用户应通过此函数记录日志。

#### 参数

- `s` (str): 日志消息
- `catelog` (str): 日志类别（必须是 `AllCatelogs` 中的一项）

#### 返回值

- 返回 `LogMan.__call__()` 的结果（无显式返回值）

#### 行为流程

1. 尝试从 `public_data` 获取已存在的 `logman` 实例
2. 若未找到：
   - 获取程序运行路径 `ProgramPath`（也来自 `public_data`）
   - 若路径不存在，抛出异常
   - 创建 `MyLog` 实例，指向该路径
   - 创建 `LogMan` 实例
   - 注册名为 `'mylog'` 的日志处理器，绑定 `MyLog` 实例，并监听所有类别
   - 将 `logman` 实例存回 `public_data`，实现单例
3. 调用 `logman(s, catelog)` 分发日志

> ✅ 优点：首次调用自动初始化，后续调用复用实例，线程不安全但适用于单线程场景。

---

## 使用示例

```python
# 记录一条普通应用信息
mylog("程序启动完成")

# 记录警告信息
mylog("磁盘空间不足", catelog='APPWarn')

# 记录系统错误
mylog("数据库连接失败", catelog='SYSError')

# 记录调试信息
mylog("变量x的值为: 123", catelog='DEBUG2')
```

日志将写入文件：`./log/my.log`，内容类似：

```
2025-04-05 10:30:45 程序启动完成
2025-04-05 10:31:12 磁盘空间不足
2025-04-05 10:31:15 数据库连接失败
2025-04-05 10:31:16 变量x的值为: 123
```

---

## 注意事项

1. ❗ **缩进错误**：
   ```python
   def setLogPath(self, path='.'):
       self.myLogPath = path
   logp = os.path.join(path, 'log')
   mkdir(logp)
   ```
   上述代码中 `logp=...` 和 `mkdir(...)` 不在方法体内部！这会导致语法错误或运行时错误。  
   ✅ 正确写法应为：
   ```python
   def setLogPath(self, path='.'):
       self.myLogPath = path
       logp = os.path.join(path, 'log')
       mkdir(logp)
   ```

2. 📁 **目录权限**：
   - 确保程序对目标路径有写权限，否则 `open()` 将失败。

3. 🔐 **线程安全**：
   - 当前实现未考虑多线程并发写日志的问题，可能造成日志混乱。
   - 建议在高并发环境下增加文件锁或改用标准库 `logging` 模块。

4. 💾 **性能考量**：
   - 每次写日志都打开/关闭文件，频繁 I/O 可能影响性能。
   - 可优化为缓存文件句柄或异步写入。

5. 🔧 **扩展建议**：
   - 支持按日期分割日志文件（如 `my_2025-04-05.log`）
   - 添加日志级别阈值控制（如仅输出 `>= APPWarn` 的日志）
   - 替换为 Python 标准 `logging` 模块以获得更强大功能

---

## 总结

本日志系统虽然简单，但具备基本的分类、注册、分发能力，适合小型项目快速集成。通过 `public_data` 实现了全局单例管理，降低了使用复杂度。但在健壮性、性能和可维护性方面仍有提升空间。

建议在生产环境中替换为 Python 内置的 `logging` 模块，或在此基础上完善异常处理与资源管理机制。