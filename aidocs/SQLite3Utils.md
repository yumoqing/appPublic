# SQLite3 数据库操作模块技术文档

## 概述

该模块提供了一个轻量级的 SQLite3 数据库封装类 `SQLite3`，支持多线程安全访问、字符编码转换（本地化与 UTF-8）、自动数据库路径管理，并通过 `Record` 类将查询结果封装为对象。模块还集成了日志记录和公共数据存储机制。

主要功能包括：
- 自动连接与重连数据库
- 多线程隔离属性管理
- SQL 执行与结果遍历
- 表结构查询（表名、字段）
- 事务控制（提交、回滚）
- 字符串编码处理（str ↔ unicode）
- 数据库路径自动生成与缓存

---

## 模块依赖

```python
import os, sys
import thread
from sqlite3 import dbapi2 as sqlite
import time
from localefunc import *
from folderUtils import mkdir
from PublicData import public_data
from mylog import mylog
```

### 第三方/内部模块说明：

| 模块 | 功能 |
|------|------|
| `localefunc` | 提供 `localeString()` 和 `local_encoding` 变量，用于本地字符串处理 |
| `folderUtils.mkdir` | 确保目录存在（创建目录） |
| `PublicData.public_data` | 全局共享数据容器，用于缓存数据库实例和路径 |
| `mylog` | 日志输出函数 |

---

## 公共函数

### `logit(s)`
记录当前文件名及消息到日志系统。

**参数：**
- `s` (str) - 要记录的日志内容

**示例：**
```python
logit("初始化数据库")
# 输出: __file__: 初始化数据库
```

---

### `str2unicode(s)`
将字符串转换为 Unicode，尝试使用本地编码或 UTF-8 解码。

**参数：**
- `s` (str 或其他类型) - 输入字符串

**返回值：**
- 成功时返回 `unicode` 对象
- 若解码失败，则返回 `buffer(s)`
- 非字符串类型原样返回

**编码优先级：**
1. `local_encoding`（来自 `localefunc`）
2. `'utf8'`
3. fallback 到 `buffer`

---

### `unicode2str(s)`
将 Unicode 或其他类型转换为适合输出的字符串形式。

**参数：**
- `s` - 待转换的数据

**返回值：**
| 类型 | 转换方式 |
|------|---------|
| `int` / `long` | 返回 `long(s)` |
| `buffer` | 转为 `str(s)` |
| `unicode` | `.encode('utf8')` |
| 其他 | 原样返回 |

---

### `argConvert(args)`
递归地将参数中的字符串转为 Unicode，支持多种数据结构。

**参数：**
- `args` - 可为 `tuple`, `list`, `dict`, 或单个值

**行为：**
- 列表或元组 → 对每个元素调用 `str2unicode`
- 字典 → 对每个值调用 `str2unicode`
- None → 返回 None
- 其他 → 直接返回

**用途：** 在执行 SQL 前统一编码格式

---

## 核心类：`Record`

表示一条数据库记录，字段作为属性访问。

### 构造函数：`__init__(self, data, localize=False)`
**参数：**
- `data` (dict) - 键值对数据（如从数据库取出）
- `localize` (bool) - 是否对字符串字段应用 `localeString()`

**逻辑：**
- 所有键名转小写后设为对象属性
- 若 `localize=True` 且值是字符串，则调用 `localeString()`

**示例：**
```python
r = Record({'Name': '张三', 'Age': 25}, localize=True)
print(r.name)  # 输出经过 localeString 处理后的名字
print(r.age)   # 25
```

### `__getattr__(self, name)`
实现属性访问时统一转为小写。

> ⚠️ **注意：此方法存在无限递归风险！**
>
> 实现中直接调用了 `getattr(self, name)` 而不是访问 `__dict__`，会导致死循环。
>
> ✅ 正确做法应为：
> ```python
> try:
>     return self.__dict__[name.lower()]
> except KeyError:
>     raise AttributeError(name)
> ```

---

### `__str__(self)`
返回对象所有属性的格式化字符串。

**返回格式：**
```
[field1 : value1
field2 : value2]
```

---

## 核心类：`SQLite3`

封装了 SQLite3 的连接、执行、查询等操作。

### 构造函数：`__init__(self, dbpath, localize=False)`
**参数：**
- `dbpath` (str) - 数据库文件路径
- `localize` (bool) - 查询结果是否进行本地化处理（传给 `Record`）

**初始化动作：**
- 创建线程隔离映射 `threadMap`
- 调用 `_connection(dbpath)` 建立连接

---

### 私有方法：`_connection(dbpath=None)`
重新建立数据库连接。

**参数：**
- `dbpath` - 新的数据库路径（可选）

**行为：**
- 更新 `self.dbpath`
- 创建新的 `sqlite.Connection` 和 `cursor`
- 重置 `result`, `sqlcmd`

---

### 特殊方法：`__setattr__` 和 `__getattr__`
实现**线程局部属性存储**，确保不同线程不会互相干扰属性读写。

#### 工作原理：
- 使用 `thread.get_ident()` 获取当前线程 ID
- 每个线程在 `self.threadMap[thread_id]` 中拥有独立命名空间
- 属性读写仅影响当前线程

> ✅ 这是一种模拟“线程局部变量”的方式，避免并发冲突

---

### 方法：`tables()`
获取数据库中所有用户表名。

**SQL 查询：**
```sql
SELECT * FROM sqlite_master WHERE type='table'
```

**返回值：**
- `list` of table names (`str`)

**流程：**
1. 执行查询
2. 遍历结果，提取 `.name` 字段
3. 返回表名列表

---

### 方法：`columns(tablename)`
⚠️ **存在拼写错误：形参名为 `tablenmae`，但使用了 `tablename`**

应修正为：
```python
def columns(self, tablename):
    self.SQL('select * from %s' % tablename)
    self.desc = self.results.description
    return self.desc
```

**功能：**
- 查询指定表的一条记录以获取字段描述
- 返回 `cursor.description`（包含字段名、类型等信息）

---

### 方法：`FETCHALL()`
执行 `fetchall()` 并返回全部结果。

> ❌ 当前实现有问题：
```python
r = True
r = self.cursor.fetchall()
return r
```
第一行赋值无意义，建议改为：
```python
def FETCHALL(self):
    if self.results:
        return self.cursor.fetchall()
    return []
```

---

### 方法：`_eatCursorNext()`
清空游标中未消费的结果，防止 `ProgrammingError`。

**目的：**
- 避免多次调用 `next()` 导致异常
- 在新查询前清理旧状态

**注意：** 使用 `.next()` 是旧式迭代器接口（Python 2），现代环境建议使用 `fetchone()` 或检查一致性。

---

### 方法：`SQL(cmd, args=(), retry=0)`
执行一条或多条 SQL 语句。

**参数：**
- `cmd` (str) - SQL 语句
- `args` (tuple/list/dict) - 参数化查询参数
- `retry` (int) - 重试次数（未实际使用）

**逻辑：**
1. 若连接断开，自动重连并重试
2. 清理上一次游标残留
3. 转换参数编码（`argConvert`）
4. 如果含多个语句（`;` 分隔），使用 `executescript`
5. 否则使用 `execute(cmd, args)`
6. 记录 `lastSQL` 和 `description`

**异常处理：**
- 打印错误信息
- 抛出原始异常

---

### 方法：`FETCH()`
逐行获取查询结果，每行封装为 `Record` 对象。

**返回值：**
- 成功 → `Record` 实例
- 结束 → `None`
- 出错 → 抛出异常

**流程：**
1. 检查是否有结果集
2. 获取 `description`（字段元信息）
3. 调用 `.next()` 获取下一行
4. 映射字段名 → 值，并用 `unicode2str` 转码
5. 构造 `Record(data, self.localize)`

---

### 方法：`COMMIT()`
提交事务，并设置大小写敏感 LIKE 匹配。

**执行命令：**
```sql
PRAGMA case_sensitive_like = 1;
```

> ✅ 注意：即使没有显式 BEGIN，SQLite 默认自动提交模式下也需 COMMIT 显式结束事务

此外还会尝试 `fetchall()` 清空结果，避免挂起。

---

### 方法：`ROLLBACK()`
执行回滚操作。

```python
self.SQL('ROLLBACK')
```

---

### 方法：`BEGIN()`
预留方法，目前为空。

> ⚠️ 注释掉 `self.SQL('BEGIN')`，可能导致事务未正确开启  
> ✅ 建议启用：
```python
def BEGIN(self):
    self.SQL('BEGIN')
```

---

### 方法：`CLOSE()`
关闭数据库连接。

**动作：**
- 设置 `self.con = None`
- 设置 `self.cursor = None`

> ⚠️ 不会自动提交或回滚，调用前请手动处理事务

---

## 辅助函数：`getDataBase(name)`

根据名称获取或创建一个全局唯一的数据库连接实例。

**参数：**
- `name` (str) - 数据库标识名（如 `'main'`, `'user'`）

**工作流程：**
1. 查找缓存 `public_data['db_main']`
2. 若不存在：
   - 查找路径 `dbpath_main`
   - 若仍不存在：
     - 使用 `ProgramPath` + `var/xxx.db3` 自动生成路径
     - 创建目录（`mkdir(var)`）
     - 缓存路径
   - 实例化 `SQLite3(dbpath)`
   - 缓存数据库实例
3. 检查连接有效性，必要时重连
4. 返回数据库对象

**优势：**
- 单例模式，避免重复打开
- 自动路径管理
- 支持热修复断连

---

## 使用示例

```python
# 获取数据库实例
db = getDataBase('test')

# 查询表
db.SQL("SELECT * FROM users WHERE age > ?", (18,))
while True:
    row = db.FETCH()
    if not row:
        break
    print(row.name, row.age)

# 插入数据（事务）
db.BEGIN()
db.SQL("INSERT INTO users(name,age) VALUES (?,?)", ("Alice", 25))
db.COMMIT()

# 获取所有表
tables = db.tables()
print(tables)
```

---

## 已知问题与改进建议

| 问题 | 描述 | 建议修复 |
|------|------|--------|
| `__getattr__` 死循环 | 调用自身导致无限递归 | 改为访问 `self.__dict__` |
| `columns()` 拼写错误 | 参数名 `tablenmae` ≠ 使用 `tablename` | 更正拼写 |
| `FETCHALL()` 逻辑冗余 | 初始赋值无效 | 简化代码 |
| `BEGIN()` 为空 | 无法开启事务 | 启用 `self.SQL('BEGIN')` |
| 异常捕获过于宽泛 | `except:` 隐藏错误 | 改为具体异常类型 |
| Python 2 风格 | 使用 `thread`, `next()` | 迁移到 `threading`, `fetchone()` |

---

## 总结

本模块是一个适用于中小型项目的 SQLite 封装工具，具备以下优点：

✅ 自动路径生成与缓存  
✅ 多线程安全属性隔离  
✅ 编码自动转换（兼容中文）  
✅ 简洁的面向对象查询接口  

⚠️ 存在若干 bug 和设计瑕疵，建议在正式项目中审慎使用，并优先修复上述问题。

---

**最后更新时间：** `{{ 自动生成时间 }}`  
**作者：** 自动生成文档 by AI  
**适用版本：** Python 2.x（因使用 `thread` 和 `next()`）