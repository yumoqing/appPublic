# AppLogger 技术文档

## 概述

`AppLogger` 是一个基于 Python 标准库 `logging` 模块封装的日志工具模块，旨在简化日志系统的初始化与使用。它提供全局日志实例、便捷的函数式接口以及面向对象的日志类，支持控制台输出和文件输出，并可自定义日志级别与格式。

---

## 功能特性

- 支持常见的日志级别：`debug`, `info`, `warning`, `error`, `critical`
- 可选日志输出方式：控制台（默认）或文件
- 全局单例模式管理日志器，避免重复创建
- 提供函数式调用接口（如 `info()`, `debug()` 等）
- 提供面向对象的 `AppLogger` 类，便于在项目中集成
- 自定义日志格式和时间戳

---

## 依赖说明

### 外部依赖

```python
import os
import sys
import logging
from functools import partial
```

### 内部依赖

```python
from appPublic.timeUtils import timestampstr
```

> 注意：`timestampstr` 在当前代码中未被实际调用，可能是预留功能或冗余导入。

---

## 配置常量

### 日志级别映射表

```python
levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,  # 原始代码有误，应为 logging.ERROR 而非 logging.error
    "critical": logging.CRITICAL
}
```

将字符串级别的名称映射为 `logging` 模块对应的标准级别常量。

> ⚠️ Bug 提示：原始代码中 `"error": logging.error` 是错误的！`logging.error` 是一个方法，不是常量。正确应为 `logging.ERROR`。

---

### 默认日志格式

```python
defaultfmt = '%(asctime)s[%(name)s][%(levelname)s][%(filename)s:%(lineno)s]%(message)s'
```

#### 格式说明：

| 占位符 | 含义 |
|--------|------|
| `%(asctime)s` | 时间戳（自动格式化） |
| `%(name)s` | Logger 名称 |
| `%(levelname)s` | 日志级别（如 INFO, DEBUG） |
| `%(filename)s` | 发出日志的源文件名 |
| `%(lineno)s` | 发出日志的行号 |
| `%(message)s` | 日志内容 |

示例输出：
```
2025-04-05 10:23:45,123[MyApp][INFO][main.py:42]Application started successfully.
```

---

### 全局变量

| 变量名       | 类型     | 初始值         | 说明 |
|-------------|----------|----------------|------|
| `logfile`   | str / None / int | `-1`           | 记录日志文件路径；`-1` 表示尚未设置，`None` 表示输出到控制台 |
| `logger`    | Logger or None | `None`         | 全局 logger 实例 |
| `g_levelname` | str      | `'info'`       | 当前日志级别名称（字符串） |
| `level`     | int      | `logging.INFO` | 对应的日志级别数值 |

---

## 核心函数

### `create_logger(name, formater=defaultfmt, levelname=None, file=None)`

创建并返回一个配置好的 `Logger` 实例。采用单例模式，确保多次调用只创建一次。

#### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | str | 是 | 无 | 日志记录器名称，通常为模块或类名 |
| `formater` | str | 否 | `defaultfmt` | 日志输出格式字符串 |
| `levelname` | str | 否 | `None` | 指定日志级别（如 `'debug'`, `'warning'`），若不传则使用全局 `g_levelname` |
| `file` | str or None | 否 | `None` | 日志输出文件路径。若为 `None`，则输出到控制台 |

#### 返回值

- `logging.Logger`：已配置的日志记录器实例

#### 行为逻辑

1. 若 `logfile == -1`（首次调用），则设置 `logfile = file`
2. 若 `logger` 已存在，则直接返回，防止重复初始化
3. 创建 `Logger` 实例
4. 设置日志级别：
   - 若传入 `levelname`，更新全局 `g_levelname` 和 `level`
   - 否则使用当前全局级别
5. 创建 `Formatter` 使用指定格式
6. 创建处理器：
   - 若 `logfile` 不为 `None` → 使用 `FileHandler`
   - 否则 → 使用 `StreamHandler`（标准输出）
7. 为处理器设置格式并添加到 logger
8. 返回 logger

> ✅ 支持热切换日志文件路径（仅限第一次）

---

### 函数式日志接口

提供顶层函数用于快速写日志，无需显式获取 logger。

| 函数 | 说明 |
|------|------|
| `info(*args, **kw)` | 输出 `INFO` 级别日志 |
| `debug(*args, **kw)` | 输出 `DEBUG` 级别日志 |
| `warning(*args, **kw)` | 输出 `WARNING` 级别日志 |
| `error(*args, **kw)` | 输出 `ERROR` 级别日志 |
| `critical(*args, **kw)` | 输出 `CRITICAL` 级别日志 |
| `exception(*args, **kw)` | 输出异常堆栈信息（等价于 `logger.exception()`） |

> ⚠️ Bug 提示：`warning()` 函数中参数拼错：`*aegs` 应为 `*args`

#### 示例

```python
from your_module import info, error

info("程序启动")
error("发生错误", exc_info=True)
```

> 注：所有函数内部检查 `if logger is None`，若未初始化则静默忽略。

---

## 类：`AppLogger`

面向对象风格的日志封装类，每个实例拥有独立但共享配置的 logger。

### 初始化

```python
def __init__(self):
    self.logger = create_logger(self.__class__.__name__)
    self.debug = self.logger.debug
    self.info = self.logger.info
    self.warning = self.logger.warning
    self.error = self.logger.error
    self.critical = self.logger.critical
    self.exception = self.logger.exception
```

#### 特性

- 使用类名作为 logger 名称（例如 `AppLogger` 实例的日志名为 `"AppLogger"`）
- 将 logger 的方法绑定到自身属性，实现链式调用
- 所有实例共用同一个底层 logger（因 `create_logger` 是单例）

### 使用示例

```python
class MyApp:
    def __init__(self):
        self.log = AppLogger()

    def run(self):
        self.log.info("应用正在运行")
        try:
            1 / 0
        except Exception as e:
            self.log.exception("捕获异常")

app = MyApp()
app.run()
```

输出示例：
```
2025-04-05 10:30:12,456[AppLogger][ERROR][myapp.py:15]捕获异常
Traceback (most recent call last):
  File "myapp.py", line 14, in run
    1 / 0
ZeroDivisionError: division by zero
```

---

## 已知问题（Bug）与改进建议

| 问题 | 描述 | 建议修复 |
|------|------|---------|
| ❌ `levels["error"]` 错误 | 使用了 `logging.error` 方法而非常量 `logging.ERROR` | 改为 `"error": logging.ERROR` |
| ❌ `warning()` 函数参数拼写错误 | `*aegs` 应为 `*args` | 修正拼写 |
| ⚠️ `exception()` 参数错误 | 调用时写成 `logger.exception(**args, **kw)` | 应为 `logger.exception(*args, **kw)`，且通常只需 `exc_info=True` |
| ⚠️ 全局状态耦合 | 多次调用 `create_logger` 无法更改 `file` 或 `format` | 可考虑增加重置机制或移除单例限制 |
| 💡 缺少关闭资源接口 | 未提供关闭 handler 的方法 | 建议添加 `close_logger()` 清理文件句柄 |

---

## 使用示例

### 示例 1：基础使用（控制台输出）

```python
from your_module import create_logger, info, debug

# 初始化 logger
create_logger("MyApp", levelname="debug")

# 使用函数接口
info("这是信息")
debug("这是调试消息")
```

### 示例 2：输出到文件

```python
from your_module import create_logger, error

create_logger("MyService", levelname="warning", file="logs/app.log")
error("发生严重错误！")
```

### 示例 3：使用 AppLogger 类

```python
from your_module import AppLogger

class DataProcessor:
    def __init__(self):
        self.log = AppLogger()
    
    def process(self):
        self.log.info("开始处理数据")
        self.log.warning("发现可疑数据点")

dp = DataProcessor()
dp.process()
```

---

## 总结

本模块通过封装 `logging` 模块，提供了简洁易用的日志接口，适用于中小型项目的快速开发。虽然存在少量 bug 和设计局限，但整体结构清晰，扩展性强。

建议在正式使用前修复已知问题，并根据需要增强配置灵活性（如支持多 handler、动态调整级别等）。

---

📌 **版本建议**：v1.0.1（需修复 bug 后发布）  
📅 **最后更新**：2025年4月5日