# 异步编程辅助工具库技术文档

```markdown
# Async Utility Toolkit

一个用于简化同步与异步函数混合使用的 Python 工具库，提供函数装饰器和异步工作池管理功能，支持将阻塞函数 `await` 化、统一处理协程与普通函数调用，并通过信号量控制并发任务数量。

---

## 模块依赖

- `time`
- `random`
- `asyncio`
- `inspect`
- `concurrent.futures`
- `functools.wraps`

> ⚠️ 注意：需要 Python 3.7+ 支持完整的 `asyncio` 特性。

---

## 核心功能概览

| 功能 | 说明 |
|------|------|
| `@awaitify` 装饰器 | 将同步函数包装为可 `await` 的异步函数，在线程池中执行以避免阻塞事件循环 |
| `@to_func` 装饰器 | 统一处理同步/异步函数调用，返回 `Future` 或直接结果 |
| `AsyncWorker` 类 | 并发控制的工作池，限制最大同时运行的任务数 |

---

## 1. `awaitify(sync_func)` —— 同步函数转异步可等待对象

### 功能描述

将任意**同步（阻塞）函数**包装成一个 **`async` 函数**，使其可以在 `async/await` 环境中被 `await` 调用。内部使用线程池执行原函数，防止阻塞主事件循环。

### 使用场景

适用于 CPU 密集型或长时间 I/O 阻塞的同步函数（如文件读写、数据库操作、`time.sleep()` 等），希望在异步程序中非阻塞地调用它们。

### 参数

- `sync_func`: 任意同步可调用对象（函数、方法等）

### 返回值

返回一个新的 `async def` 函数，签名与原函数一致。

### 示例代码

```python
def hello(cnt, greeting):
    t = random.randint(1, 10)
    print(cnt, 'will sleep ', t, 'seconds')
    time.sleep(t)  # 阻塞操作
    print(cnt, 'cost ', t, 'seconds to', greeting)

# 包装为异步函数
f = awaitify(hello)

# 可以在协程中 await
await f(1, "hello world")
```

### 实现原理

1. 获取当前或创建新的事件循环。
2. 使用 `ThreadPoolExecutor` 在后台线程中执行原始函数。
3. 使用 `loop.run_in_executor()` 将其调度为异步任务并 `await` 结果。

> ✅ 安全地将阻塞调用移出主线程，不阻塞事件循环。

---

## 2. `to_func(func)` —— 统一同步/异步函数接口

### 功能描述

装饰一个函数，使其无论是否是协程函数（`async def`），都能通过统一方式调用并返回一个可等待的对象（`Future` / `Task`）。主要用于兼容不同类型的回调或任务提交。

### 参数

- `func`: 待包装的函数，可以是同步函数或 `async def` 协程函数。

### 返回值

- 若 `func` 是协程函数：返回一个由 `asyncio.gather(task)` 包装的 `Future`
- 否则：直接返回函数执行结果

⚠️ 当前实现中，对协程函数返回的是 `gather(task)`，这会立即启动任务但不会自动 `await`，需注意上下文中的事件循环管理。

### 示例代码

```python
@to_func
async def ahello():
    await asyncio.sleep(1)
    return "done"

result = ahello()  # 返回一个 Future 对象
await result       # 可 await 获取结果
```

> ❗ 注意：此装饰器设计存在一定歧义（同步函数返回值 vs 异步返回 Future），建议仅用于特定调度系统集成。

---

## 3. `AsyncWorker` —— 并发任务控制器

### 类定义

```python
class AsyncWorker:
    def __init__(self, maxtask=50)
    async def __call__(self, callee, *args, **kw)
    async def run(self, cmd)
```

### 构造函数：`__init__(maxtask=50)`

#### 参数

- `maxtask` (int): 最大并发任务数，默认为 50。

#### 功能

初始化一个 `asyncio.Semaphore` 信号量，用于限制同时执行的任务数量。

---

### 方法：`__call__(callee, *args, **kw)`

允许将 `AsyncWorker` 实例当作异步函数调用，自动限流执行目标函数。

#### 参数

- `callee`: 被调用的函数，支持同步或异步函数
- `*args`, `**kw`: 传递给 `callee` 的参数

#### 行为逻辑

1. 获取信号量（控制并发）
2. 判断 `callee` 是否为协程函数：
   - 是：`await` 执行
   - 否：直接调用（若为阻塞函数仍可能影响性能）

#### 示例

```python
w = AsyncWorker(maxtask=10)
await w(hello, i, "hello world")  # 自动限流执行
```

> 🔒 每次最多只有 `maxtask` 个任务在运行。

---

### 方法：`run(cmd)`

异步执行 shell 命令，捕获标准输出和错误输出。

#### 参数

- `cmd` (str): 要执行的 Shell 命令字符串

#### 返回值

元组 `(stdout: bytes, stderr: bytes)`

#### 注意事项

> 🛑 存在一个拼写错误：`proc.comunicate()` → 应为 `proc.communicate()`

#### 正确实现应为：

```python
stdout, stderr = await proc.communicate()
```

否则会抛出 `AttributeError`。

#### 示例

```python
worker = AsyncWorker()
stdout, stderr = await worker.run("ls -la")
print(stdout.decode())
```

---

## 主程序示例（`if __name__ == '__main__':`）

演示了如何结合 `awaitify` 和 `AsyncWorker` 实现大规模并发调用同步函数。

### 流程说明

1. 定义两个函数：
   - `hello()`: 同步版本，使用 `time.sleep`
   - `ahello()`: 异步版本，使用 `await asyncio.sleep`
2. 创建 `run()` 协程函数：
   - 实例化 `AsyncWorker`
   - 使用 `awaitify(hello)` 包装同步函数
   - 创建 100 个任务并行执行
   - 使用 `asyncio.wait()` 等待所有任务完成
3. 运行事件循环直到完成。

### 输出示例

```
0 will sleep  7 seconds
1 will sleep  3 seconds
...
0 cost  7 seconds to hello world
1 cost  3 seconds to hello world
aaaaaaaaaaaaaaaaaaa
```

---

## 已知问题与改进建议

| 问题 | 描述 | 建议修复 |
|------|------|---------|
| `comunicate` 拼写错误 | 应为 `communicate` | 更正为 `await proc.communicate()` |
| 多余导入 | `from functools import wraps` 出现两次 | 删除重复行 |
| `to_func` 设计模糊 | 返回类型不一致（有时是值，有时是 Future） | 建议统一返回 `Task` 或改为上下文感知调度器 |
| `to_func` 中 `gather` 使用不当 | `asyncio.gather(task)` 单任务无意义 | 改为直接返回 `task` 或去除 `gather` |
| `to_func` 不适合通用场景 | 无法在普通函数中 `await` 返回的 `Future` | 建议仅用于事件循环内调度 |

---

## 安装与使用

无需安装，直接导入模块即可使用。

```python
from your_module import awaitify, AsyncWorker
```

---

## 总结

本工具包提供了以下核心能力：

✅ 安全地 `await` 同步阻塞函数  
✅ 控制最大并发任务数  
✅ 简化异步 Shell 命令执行  
✅ 提供基本的同步/异步调用统一接口（有待优化）

适合用于爬虫、批量任务处理、微服务中间层等需要混合同步异步逻辑的场景。

---
```

> 💡 **提示**：生产环境中建议增加日志记录、异常处理、超时机制以及更完善的单元测试。