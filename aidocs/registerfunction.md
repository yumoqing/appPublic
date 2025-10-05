# 技术文档：函数与协程注册系统

## 概述

本模块提供了一套基于单例模式的**函数注册**和**协程执行管理**机制，支持同步函数与异步协程的统一注册、获取与调用。通过 `RegisterFunction` 和 `RegisterCoroutine` 两个核心类，实现了灵活的插件式函数调用架构。

该系统适用于需要动态注册和调用函数/协程的场景（如事件处理器、中间件链、插件系统等），并保证全局唯一实例（单例）。

---

## 模块依赖

```python
import asyncio
from inspect import isfunction, iscoroutinefunction
from functools import partial
from appPublic.dictObject import DictObject
from appPublic.worker import awaitify
from appPublic.Singleton import SingletonDecorator
from appPublic.log import info, error
```

### 第三方/自定义组件说明：

| 包/模块 | 功能 |
|--------|------|
| `appPublic.dictObject.DictObject` | 可属性访问的字典对象，用于存储键值对数据 |
| `appPublic.worker.awaitify` | 将同步函数包装为可被 `await` 调用的形式 |
| `appPublic.Singleton.SingletonDecorator` | 单例装饰器，确保类仅有一个实例 |
| `appPublic.log.info`, `.error` | 日志输出工具 |

---

## 核心类

### 1. `RegisterFunction` —— 函数注册中心（单例）

> 装饰器：`@SingletonDecorator`  
> 用途：注册、获取并执行命名的函数或协程。

#### 属性

- `registKW` (dict): 存储注册的函数，键为名称，值为函数对象。

#### 方法

##### `__init__(self)`
初始化空的函数注册表。

##### `register(name: str, func: callable)`
将一个函数或协程注册到指定名称下。

- **参数**：
  - `name` (str): 函数的唯一标识名。
  - `func` (callable): 要注册的函数或异步协程。
- **行为**：
  - 若 `func` 不是函数或协程，则记录错误日志并返回。
  - 同名函数会被覆盖（最新注册者胜出）。
- **示例**：
  ```python
  rf = RegisterFunction()
  rf.register("hello", lambda: print("Hello"))
  ```

##### `get(name: str) -> Optional[callable]`
根据名称获取已注册的函数。

- **返回**：函数对象，若未找到则返回 `None`。

##### `run(name: str, *args, **kw)`
**同步执行**指定名称的函数。

- **注意**：
  - 如果目标是协程函数（`async def`），会打印提示但不执行，并返回 `None`。
  - 仅适用于普通同步函数。
- **返回**：函数执行结果。
- **异常处理**：若函数未注册，输出错误日志。

##### `async exe(name: str, *args, **kw) -> Any`
**异步安全执行**指定名称的函数或协程。

- **逻辑**：
  - 若函数是协程（`iscoroutinefunction`），直接 `await` 执行。
  - 若是普通函数，使用 `awaitify` 包装后执行（使其可在异步上下文中调用）。
- **返回**：函数执行结果（支持 `await`）。
- **失败处理**：函数不存在时返回 `None`（静默失败）。

---

### 2. `RegisterCoroutine` —— 协程链注册中心（单例）

> 装饰器：`@SingletonDecorator`  
> 用途：按名称注册多个函数/协程，并以**逆序方式批量执行**（类似中间件栈）。

#### 属性

- `kw` (`DictObject`): 内部存储结构，每个名字对应一个函数列表。

#### 方法

##### `__init__(self)`
初始化一个空的 `DictObject` 来保存函数列表。

##### `register(name: str, func: callable)`
向指定名称追加一个函数或协程。

- **行为**：
  - 验证输入是否为合法函数。
  - 若该名称尚无注册项，则创建新列表 `[func]`。
  - 否则将 `func` 追加至列表末尾。
- **特点**：支持同一名称注册多个处理器。

##### `async exe(name: str, *args, **kw)`
异步执行该名称下所有注册的函数/协程，顺序为**后进先出（LIFO）**。

- **流程**：
  1. 获取函数列表副本。
  2. 反转列表（实现 LIFO 执行）。
  3. 遍历执行每一个函数：
     - 协程：`await f(*args, **kw)`
     - 普通函数：直接调用 `f(*args, **kw)`
- **返回**：始终返回 `None`。
- **说明**：适合用于事件通知、钩子机制等无需聚合返回值的场景。

---

## 辅助函数

以下函数提供便捷接口，避免手动实例化单例。

### `getRegisterFunctionByName(name: str) -> Optional[callable]`
获取已注册的函数对象。

- **参数**：`name` – 函数名
- **返回**：函数引用或 `None`

### `registerFunction(name: str, func: callable)`
快捷注册函数。

- **等价于**：
  ```python
  RegisterFunction().register(name, func)
  ```

### `async rfexe(rfname: str, *args, **kw) -> Any`
异步执行指定名称的注册函数。

- **等价于**：
  ```python
  await RegisterFunction().exe(rfname, *args, **kw)
  ```

### `rfrun(rfname: str, *args, **kw) -> Any`
同步执行注册函数（仅限同步函数）。

- **等价于**：
  ```python
  RegisterFunction().run(rfname, *args, **kw)
  ```

---

## 使用示例

```python
# 定义测试函数
def x(dic):
    dic['a'] = 'a'
    return dic

async def y(dic):
    dic['b'] = 'b'
    return dic

def z(dic):
    dic['c'] = 1
    return dic

# 主程序
async def main():
    rf = RegisterCoroutine()
    rf.register('test', z)
    rf.register('test', y)
    rf.register('test', x)

    d = {}
    await rf.exe('test', d)  # 按 x → y → z 的反向顺序执行
    print(d)  # 输出: {'a': 'a', 'b': 'b', 'c': 1}

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
```

> ⚠️ 注意：由于 `exe()` 中反转了函数列表，实际执行顺序为最后注册的最先执行。

---

## 设计亮点

| 特性 | 描述 |
|------|------|
| ✅ **单例模式** | 使用 `SingletonDecorator` 确保全局唯一实例，便于跨模块共享注册表 |
| ✅ **兼容同步与异步** | 自动识别协程函数并通过 `awaitify` 统一异步调用接口 |
| ✅ **类型安全检查** | 注册时验证是否为合法函数，防止误注册非可调用对象 |
| ✅ **灵活调用方式** | 提供同步 `run` 与异步 `exe` 接口，适应不同运行环境 |
| ✅ **链式协程支持** | `RegisterCoroutine` 支持多函数绑定与逆序执行，适用于中间件/钩子系统 |

---

## 注意事项

1. **协程不能用 `run()` 执行**：`run()` 方法不会 `await` 协程，可能导致警告或无效执行。
2. **函数覆盖问题**：`RegisterFunction.register()` 是覆盖式注册，同名函数旧版本将丢失。
3. **异常捕获建议**：当前未封装异常处理，在生产环境中建议在 `exe()` 外层添加 try-except。
4. **性能考虑**：频繁注册可能导致内存增长，长期运行服务应定期清理无用条目。

---

## 总结

本模块构建了一个轻量级、高内聚的函数调度系统，特别适用于：

- 插件化系统
- 事件驱动架构
- 中间件管道设计
- 异步任务调度

结合 `awaitify` 与单例模式，实现了简洁而强大的函数注册与异步执行能力，具备良好的扩展性和复用性。