# `ProcessWorkers` 类技术文档

## 概述

`ProcessWorkers` 是一个基于多进程和线程信号量控制的并发任务调度类，用于限制同时运行的进程数量。它通过 `multiprocessing.Process` 创建独立进程执行任务，并使用 `threading.Semaphore` 控制并发工作进程的数量。

该类适用于需要控制并发资源占用（如 CPU 密集型任务）且希望避免系统过载的场景。

---

## 依赖说明

```python
import time
from multiprocessing import Process
import threading
import random
from appPublic.background import Background
```

- **`time`**: 用于模拟任务延迟。
- **`multiprocessing.Process`**: 用于创建独立子进程执行任务。
- **`threading.Semaphore`**: 限制最大并发工作进程数。
- **`random`**: 示例中用于生成随机等待时间。
- **`appPublic.background.Background`**: 封装异步启动功能，使 `.do()` 方法非阻塞。

> ⚠️ 注意：`appPublic` 是自定义模块，需确保其在项目路径中可用。

---

## 类定义：`ProcessWorkers`

```python
class ProcessWorkers:
    def __init__(self, worker_cnt=10):
        self.semaphore = threading.Semaphore(value=worker_cnt)
        self.co_worker = 0
```

### 初始化参数

| 参数名       | 类型   | 默认值 | 说明 |
|------------|--------|-------|------|
| `worker_cnt` | `int`  | `10`  | 允许同时运行的最大工作进程数量 |

### 属性说明

| 属性名         | 类型               | 说明 |
|--------------|--------------------|------|
| `semaphore`  | `threading.Semaphore` | 控制并发进程数的信号量对象 |
| `co_worker`  | `int`              | 当前正在运行的工作进程计数器（线程不安全读写，仅作粗略参考） |

> 🔔 提示：`co_worker` 的增减未加锁，在高并发下可能产生竞态条件，建议仅用于调试或监控目的。

---

## 方法说明

### `_do(func, *args, **kwargs)`

**私有方法**：实际执行任务的逻辑。

#### 参数

| 参数名     | 类型       | 说明 |
|----------|------------|------|
| `func`   | `callable` | 要在子进程中执行的函数 |
| `*args`  | 可变位置参数 | 传递给 `func` 的位置参数 |
| `**kwargs` | 可变关键字参数 | 传递给 `func` 的关键字参数 |

#### 执行流程

1. 获取信号量（若已达上限则阻塞等待）；
2. 增加 `co_worker` 计数；
3. 创建并启动新进程执行 `func(*args, **kwargs)`；
4. 主进程阻塞等待子进程完成（`p.join()`）；
5. 减少 `co_worker` 计数；
6. 释放信号量，允许其他任务进入。

#### 特性

- 子进程与主进程内存隔离；
- 使用 `join()` 阻塞当前线程直到进程结束；
- 确保最多只有 `worker_cnt` 个进程同时运行。

> ⚠️ 性能提示：由于 `p.join()` 在 `_do` 中同步调用，每个后台线程将阻塞直至任务完成。

---

### `do(func, *args, **kwargs)`

**公有方法**：异步提交任务。

#### 参数

同 `_do` 方法。

#### 功能描述

使用 `Background` 类将 `_do` 包装为后台线程执行，实现非阻塞提交任务。

```python
b = Background(self._do, func, *args, **kwargs)
b.start()
```

> ✅ 效果：调用 `do()` 后立即返回，任务在后台线程中以进程方式运行。

---

### `get_workers()`

获取当前正在运行的任务数量。

#### 返回值

- 类型：`int`
- 内容：当前 `co_worker` 的值（即已开始但尚未结束的任务数）

> ⚠️ 注意：此数值为近似值，因无锁保护可能存在竞争问题。

---

## 使用示例

```python
if __name__ == '__main__':
    def k(worker):
        t = random.randint(1, 4)
        print('current workers=', worker.get_workers(), 'sleep=', t)
        time.sleep(t)

    w = ProcessWorkers(worker_cnt=5)  # 最多5个并发进程
    for i in range(100):
        w.do(k, w)
```

### 输出示例（部分）

```
current workers= 1 sleep= 3
current workers= 2 sleep= 1
current workers= 3 sleep= 4
...
```

### 行为分析

- 每次 `w.do(k, w)` 提交一个耗时 1~4 秒的任务；
- 最多同时运行 5 个进程；
- 使用 `Background` 实现异步提交，循环无需等待单个任务完成；
- `get_workers()` 显示当前活跃进程数。

---

## 设计特点与注意事项

### ✅ 优点

| 特性 | 说明 |
|------|------|
| **资源控制** | 通过信号量严格限制并发进程数，防止系统过载 |
| **进程级隔离** | 利用 `multiprocessing` 避免 GIL 影响，适合 CPU 密集型任务 |
| **异步接口** | `do()` 方法非阻塞，支持快速批量提交任务 |

### ❗️局限性与风险

| 问题 | 说明 |
|------|------|
| `co_worker` 线程安全缺失 | 多线程修改未加锁，可能导致计数错误 |
| `p.join()` 阻塞线程 | `_do` 在后台线程中仍会阻塞，无法进一步提升吞吐 |
| 进程开销较大 | 对于轻量任务，频繁创建/销毁进程影响性能 |
| 错误处理缺失 | 未捕获异常，崩溃任务可能导致状态不一致 |

---

## 改进建议

1. **添加线程锁保护共享变量**

```python
def __init__(self, worker_cnt=10):
    self.semaphore = threading.Semaphore(value=worker_cnt)
    self.co_worker = 0
    self._lock = threading.Lock()

def _do(self, func, *args, **kwargs):
    self.semaphore.acquire()
    with self._lock:
        self.co_worker += 1
    try:
        p = Process(target=func, args=args, kwargs=kwargs)
        p.start()
        p.join()
    finally:
        with self._lock:
            self.co_worker -= 1
        self.semaphore.release()
```

2. **支持异常捕获与回调**

```python
def _do(self, func, *args, **kwargs):
    ...
    try:
        p = Process(...)
        p.start()
        p.join()
        if p.exitcode != 0:
            print(f"Process exited abnormally with code {p.exitcode}")
    except Exception as e:
        print(f"Failed to run process: {e}")
    finally:
        ...
```

3. **考虑使用进程池替代动态创建**

对于高频任务，推荐使用 `concurrent.futures.ProcessPoolExecutor` 或 `multiprocessing.Pool` 以减少开销。

---

## 总结

`ProcessWorkers` 提供了一种简单有效的方式管理并发进程数量，适合对并发度敏感的应用场景。虽然存在一些线程安全和性能上的不足，但结构清晰、易于理解和扩展。

| 适用场景 | 不适用场景 |
|---------|-----------|
| CPU 密集型任务调度 | I/O 密集型任务（应使用线程） |
| 需要限制系统负载的任务 | 极低延迟要求的实时系统 |
| 批量任务异步处理 | 大规模微任务处理（建议用线程池或协程） |

> 推荐作为学习多进程控制机制的基础模板，在生产环境中结合更成熟的并发框架进行优化。