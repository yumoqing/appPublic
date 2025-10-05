# `RestrictedEnv` 类技术文档

## 概述

`RestrictedEnv` 是一个轻量级的沙箱环境类，用于在受限上下文中安全地执行与日期/时间相关的表达式。它通过注册特定函数并利用 Python 的 `exec` 动态执行字符串形式的代码，提供了一种简洁的方式来解析和计算时间表达式，同时避免直接暴露完整的 Python 执行环境。

该类主要适用于需要动态解析时间表达式的场景（如配置文件、规则引擎等），且希望限制可调用函数范围以增强安全性。

---

## 依赖

- `appPublic.timeUtils as tu`：提供日期/时间格式化与解析工具函数。
- `datetime as dt`：Python 标准库中的 `datetime` 模块，用于处理日期和时间对象。

> ⚠️ 注意：确保 `appPublic.timeUtils` 模块已正确安装并包含所需方法。

---

## 类定义

```python
class RestrictedEnv:
```

### 构造函数 `__init__`

初始化 `RestrictedEnv` 实例，并注册一组预定义的时间相关函数到内部命名空间。

#### 注册的函数：
| 函数名     | 对应方法                  | 描述 |
|------------|----------------------------|------|
| `today`    | `self.today()`             | 返回今天的日期（仅年月日） |
| `date`     | `self.date(dstr)`          | 将字符串转换为日期对象 |
| `datetime` | `self.datetime(dstr)`      | 将字符串转换为 datetime 对象 |
| `now`      | `dt.datetime.now`（原生）  | 获取当前精确到微秒的日期时间 |

#### 示例：
```python
env = RestrictedEnv()
# 此时 env 已经可以识别 'today()', 'date(...)', 'datetime(...)', 'now()' 等表达式
```

---

## 方法说明

### `reg(k: str, v: callable) -> None`

将键值对 `(k, v)` 注册到实例的命名空间中，使得后续可通过字符串表达式调用 `v`。

#### 参数：
- `k` (str): 在表达式中使用的函数或变量名称。
- `v` (callable): 可调用对象（函数、方法、lambda 等）或数据。

#### 实现方式：
使用 `self.__dict__[k] = v` 将其注入局部作用域。

#### 示例：
```python
ns.reg('pi', 3.14159)
result = ns.run('pi * 2')  # 返回 6.28318
```

---

### `run(dstr: str) -> Any`

在受限环境中执行给定的表达式字符串，并返回其结果。

#### 参数：
- `dstr` (str): 要执行的表达式字符串（如 `'today()'`, `"date('2023-01-01')"`）。

#### 返回值：
表达式计算的结果。

#### 原理：
1. 将输入表达式包装为赋值语句：`__tempkey__ = <表达式>`
2. 使用 `exec()` 在全局 `globals()` 和实例局部命名空间 `self.__dict__` 中执行。
3. 返回临时变量 `self.__tempkey__` 的值。

> ✅ 安全提示：虽然名为“受限”，但由于使用了 `exec`，仍需谨慎处理不可信输入，防止代码注入风险。

#### 示例：
```python
result = ns.run("today()")        # 返回今天日期（Date 类型）
result = ns.run("now()")          # 返回当前 datetime 对象
```

---

### `today() -> date`

获取当前日期（仅年-月-日部分），忽略时间信息。

#### 返回：
- `date` 对象，由 `tu.ymdDate(year, month, day)` 生成。

#### 内部逻辑：
```python
now = dt.datetime.now()
return tu.ymdDate(now.year, now.month, now.day)
```

#### 示例：
```python
ns.run("today()")  # 输出类似: 2025-04-05
```

---

### `date(dstr: str) -> date`

将日期字符串转换为日期对象。

#### 参数：
- `dstr` (str): 格式化的日期字符串，例如 `'2023-12-25'`

#### 返回：
- `date` 对象，由 `tu.str2Date(dstr)` 解析得到。

#### 示例：
```python
ns.run("date('2023-01-01')")  # 返回对应日期对象
```

---

### `datetime(dstr: str) -> datetime`

将日期时间字符串转换为 `datetime` 对象。

#### 参数：
- `dstr` (str): 包含时间和日期的字符串，如 `"2023-06-15 14:30:00"`

#### 返回：
- `datetime` 对象，由 `tu.str2Datetime(dstr)` 解析生成。

#### 示例：
```python
ns.run('datetime("2023-07-04 12:00:00")')
```

---

## 使用示例

以下是在主模块中运行的测试代码：

```python
if __name__ == '__main__':
    ns = RestrictedEnv()
    a = ns.run('today()')                           # 当前日期
    b = ns.run("date('2011-10-31')")                # 自定义日期对象
    c = ns.run('datetime("2012-03-12 10:22:22")')   # 自定义 datetime
    d = ns.run('now()')                             # 当前完整时间戳
```

### 预期输出类型：
| 表达式 | 返回类型 | 示例值 |
|--------|----------|--------|
| `today()` | `date` | `2025-04-05` |
| `date(...)` | `date` | `2011-10-31` |
| `datetime(...)` | `datetime` | `2012-03-12 10:22:22` |
| `now()` | `datetime` | `2025-04-05 10:15:30.123456` |

---

## 安全性说明

⚠️ **警告**：尽管称为“受限环境”，但因使用了 `exec()`，若传入恶意字符串可能导致任意代码执行。

建议：
- 仅用于可信输入或受控环境。
- 不应用于解析用户提交的表达式，除非有额外语法校验层。
- 可考虑替换为更安全的表达式解析器（如 `asteval`, `simpleeval`）以提升安全性。

---

## 扩展建议

你可以通过继承或修改 `reg` 调用来扩展功能，例如添加数学函数、条件判断等：

```python
import math
ns.reg('sqrt', math.sqrt)
result = ns.run('sqrt(16)')  # 得到 4.0
```

但请始终注意作用域控制与安全性。

---

## 总结

`RestrictedEnv` 提供了一个简单而有效的方式，在隔离环境下动态求值时间表达式。适合集成于规则系统、报表脚本或配置驱动的应用程序中，作为时间处理的 DSL（领域专用语言）入口点。

| 特性 | 说明 |
|------|------|
| ✅ 易用性 | 支持自然的时间表达式写法 |
| ✅ 可扩展 | 通过 `reg()` 添加新函数 |
| ⚠️ 安全性 | 使用 `exec`，需防范注入风险 |
| 📦 轻量 | 无外部依赖（除 `appPublic.timeUtils`） |

--- 

✅ **推荐用途**：内部工具、自动化脚本、配置解析器  
❌ **不推荐用途**：Web API 输入解析、不受信用户输入处理