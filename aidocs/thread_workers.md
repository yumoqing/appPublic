# `ThreadWorkers` 技术文档

```markdown
# ThreadWorkers 模块技术文档

## 概述

`ThreadWorkers` 是一个基于 Python 多线程的轻量级任务调度类，用于控制并发执行的任务数量。它通过 `threading.Semaphore` 实现对最大工作线程数的限制，并结合后台线程（`Background`）异步执行函数任务。

该模块适用于需要控制并发度的场景，如爬虫请求、I/O 密集型操作等，防止系统资源被过度占用。

---

## 依赖说明

- **Python 标准库**：
  - `time`: 提供延时功能。
  - `threading`: 使用 `Semaphore` 控制并发，`Thread` 执行异步任务。
  - `random`: 示例中用于生成随机延迟时间。

- **第三方模块**：
  - `appPublic.background.Background`: 一个封装好的后台线程类，用于在独立线程中运行指定函数。

> ⚠️ 注意：请确保已安装并可导入 `appPublic.background` 包。

---

## 类定义：`ThreadWorkers`

### 初始化方法：`__init__(self, max_workers=10)`

#### 参数：
| 参数名        | 类型   | 默认值 | 说明 |
|-------------|--------|-------|------|
| `max_workers` | int    | 10    | 最大允许同时运行的工作线程数量 |

#### 功能：
初始化一个信号量（`Semaphore`），用于控制并发线程数量；同时初始化当前工作线程计数器 `co_worker`。

#### 示例：
```python
w = ThreadWorkers(max_workers=30)
```

---

### 私有方法：`_do(self, func, *args, **kwargs)`

#### 参数：
| 参数名   | 类型       | 说明 |
|--------|------------|------|
| `func` | callable   | 要执行的目标函数 |
| `*args`  | tuple      | 传递给目标函数的位置参数 |
| `**kwargs` | dict     | 传递给目标函数的关键字参数 |

#### 功能：
实际执行任务的方法，在获取信号量后增加工作计数，执行函数，完成后释放信号量并减少计数。

#### 流程说明：
1. 调用 `semaphore.acquire()` 等待可用线程槽位。
2. 增加 `co_worker` 计数。
3. 执行传入的函数 `func(*args, **kwargs)`。
4. 无论成功或异常，最终都会：
   - 减少 `co_worker`
   - 调用 `semaphore.release()`

> ✅ 使用 `try...finally` 结构确保即使发生异常也能正确释放资源。

---

### 公共方法：`do(self, func, *args, **kwargs)`

#### 参数：
同 `_do` 方法。

#### 功能：
将任务提交到后台异步执行。使用 `Background` 类创建一个新线程来调用 `_do` 方法，实现非阻塞式任务提交。

#### 示例：
```python
def my_task(name):
    print(f"Hello from {name}")

w.do(my_task, "Alice")
```

> 📌 此方法不会阻塞主线程，任务将在后台线程中执行。

---

### 公共方法：`get_workers(self)`

#### 返回值：
- 类型：`int`
- 含义：当前正在运行的任务数量（即活跃线程数）

#### 示例：
```python
print("Active workers:", w.get_workers())
```

---

### 公共方法：`until_done(self)`

#### 功能：
阻塞主线程，直到所有已提交的任务完成执行（即 `co_worker == 0`）。

#### 实现细节：
- 初始等待 0.1 秒。
- 循环检查 `self.co_worker > 0`，每次休眠 0.01 秒（10ms）进行轮询。

> ⚠️ 注意：此为忙等待（busy-waiting）的一种温和形式，适合短时间等待。长时间使用可能影响性能。

#### 示例：
```python
for i in range(100):
    w.do(k, w)

w.until_done()  # 等待所有任务结束
print("All tasks completed.")
```

---

## 使用示例

以下是一个完整示例，演示如何使用 `ThreadWorkers` 提交大量耗时任务并限制最大并发数：

```python
if __name__ == '__main__':
    def k(worker):
        t = random.randint(1, 4)
        print('current workers=', worker.get_workers(), 'sleep=', t)
        time.sleep(t)

    w = ThreadWorkers(max_workers=30)
    for i in range(100000):
        w.do(k, w)

    w.until_done()
    print("All done!")
```

### 输出示例：
```
current workers= 5 sleep= 3
current workers= 6 sleep= 2
...
All done!
```

---

## 设计特点与优势

| 特性 | 描述 |
|------|------|
| 🔐 并发控制 | 使用 `Semaphore` 严格限制最大并发线程数 |
| 🧮 实时监控 | 可通过 `get_workers()` 获取当前活跃任务数 |
| ⏳ 安全清理 | `until_done()` 支持优雅等待所有任务完成 |
| 💥 异常安全 | `_do` 中使用 `finally` 确保信号量和计数始终被释放 |
| 🧱 解耦设计 | 利用 `Background` 类实现任务与线程管理解耦 |

---

## 注意事项

1. **线程安全**：`co_worker` 的增减未使用锁保护，但由于其仅用于粗略统计且在 `Semaphore` 内部已有同步机制，一般情况下是安全的。若需更高精度统计，建议添加 `threading.Lock`。
   
2. **性能考量**：`until_done()` 使用轮询方式，不适合高精度实时系统。可考虑使用事件通知机制优化。

3. **资源上限**：`max_workers` 不宜设置过高，避免引发系统线程过多导致性能下降。

4. **异常处理扩展**：当前 `_do` 方法不捕获函数内部异常。如需记录错误日志，可在 `try` 块中增强异常处理逻辑。

---

## 扩展建议

- 添加任务回调支持（如 `on_success`, `on_error`）
- 支持超时机制
- 引入任务队列与线程池复用，提升效率
- 替换 `until_done` 为 `Event` 或 `Condition` 实现更高效的等待机制

---

## 总结

`ThreadWorkers` 是一个简洁高效的并发任务控制器，适用于需要简单控制并发数的异步任务场景。其设计清晰、易于使用，适合作为基础组件集成进各类后台处理系统中。
```