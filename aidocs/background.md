# `Background` 类技术文档

## 概述

`Background` 是一个基于 Python 内置 `threading.Thread` 的轻量级封装类，用于在后台线程中异步执行指定的函数。通过继承 `Thread` 类，该类能够将任意可调用对象（函数、方法等）放入独立线程中运行，避免阻塞主线程。

---

## 依赖

- Python 标准库：`threading`

```python
from threading import Thread
```

---

## 类定义

```python
class Background(Thread):
    def __init__(self, func, *args, **kw):
        Thread.__init__(self)
        self.__callee = func
        self.__args = args
        self.__kw = kw

    def run(self):
        return self.__callee(*self.__args, **self.__kw)
```

---

## 构造函数

### `__init__(self, func, *args, **kw)`

初始化一个 `Background` 实例。

#### 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `func` | `callable` | 要在后台线程中执行的函数或可调用对象。 |
| `*args` | `tuple` | 传递给 `func` 的位置参数。 |
| `**kw` | `dict` | 传递给 `func` 的关键字参数。 |

#### 示例

```python
def greet(name, message="Hello"):
    print(f"{message}, {name}!")

# 创建 Background 实例
bg_task = Background(greet, "Alice", message="Hi")
```

---

## 方法

### `run(self)`

重写自 `Thread.run()`，在调用 `start()` 时自动执行。该方法会调用构造函数中传入的 `func`，并传入指定的参数。

> ⚠️ 注意：`run()` 方法的返回值 **不会** 被线程机制捕获或传递回主线程。若需获取返回值，应结合 `queue.Queue` 或 `concurrent.futures.Future` 等机制实现。

#### 示例

```python
bg_task.start()  # 启动线程，执行 greet 函数
```

---

## 使用示例

### 基本用法

```python
import time

def long_running_task(duration):
    print("任务开始...")
    time.sleep(duration)
    print("任务完成！")

# 在后台执行耗时任务
bg = Background(long_running_task, 3)
bg.start()  # 非阻塞，立即返回

print("主线程继续运行...")

bg.join()  # 可选：等待后台任务完成
```

### 输出结果

```
任务开始...
主线程继续运行...
任务完成！
```

---

## 注意事项

1. **返回值不可直接获取**  
   `Background` 类的 `run()` 方法虽然有 `return` 语句，但线程无法直接获取其返回值。如需获取结果，请使用如下方式：

   ```python
   from queue import Queue

   def task_with_result(q):
       result = "处理完成"
       q.put(result)

   q = Queue()
   bg = Background(task_with_result, q)
   bg.start()
   bg.join()
   print(q.get())  # 获取结果
   ```

2. **异常处理**  
   若目标函数抛出异常，异常将在子线程中引发，但不会自动传播到主线程。建议在 `func` 内部进行异常捕获和日志记录。

3. **线程安全**  
   确保 `func` 中访问的资源是线程安全的，必要时使用锁（`threading.Lock`）保护共享数据。

---

## 扩展建议

- 可扩展为支持回调函数、超时控制、结果回调等功能。
- 推荐在复杂场景下使用 `concurrent.futures.ThreadPoolExecutor` 替代手动线程管理。

---

## 版本兼容性

- 支持 Python 3.6+

---

## 许可证

此代码为公共领域示例代码，可用于学习与商业用途（请根据实际项目要求添加许可证）。