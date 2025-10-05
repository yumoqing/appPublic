# 多线程任务处理框架技术文档

本项目实现了一个基于 Python `threading` 和 `queue` 模块的轻量级多线程任务调度系统，支持异步执行可调用函数（callable），适用于 I/O 密集型任务如网络请求、文件读写等。

---

## 目录

- [1. 概述](#1-概述)
- [2. 核心组件](#2-核心组件)
  - [2.1 `Worker` 类](#21-worker-类)
  - [2.2 `ThreadWorkers` 类](#22-threadworkers-类)
- [3. 使用示例](#3-使用示例)
- [4. API 参考](#4-api-参考)
- [5. 注意事项与限制](#5-注意事项与限制)
- [6. 依赖项](#6-依赖项)

---

## 1. 概述

该模块提供一个简单的线程池机制，通过预创建一组工作线程来异步执行提交的任务。所有任务通过队列传递给空闲的工作线程进行处理，避免频繁创建和销毁线程带来的开销。

主要特点：
- 支持任意可调用对象（函数、方法、lambda 等）作为任务。
- 支持传递位置参数和关键字参数。
- 提供优雅关闭机制等待所有任务完成。
- 基于标准库，无外部复杂依赖（除使用场景中引入的第三方库）。

---

## 2. 核心组件

### 2.1 `Worker` 类

`Worker` 是继承自 `threading.Thread` 的工作线程类，负责从任务队列中获取并执行任务。

#### 属性
| 属性 | 类型 | 描述 |
|------|------|------|
| `r_queue` | `Queue` | 接收任务的任务队列实例 |
| `timeout` | `int/float` | 获取任务时的超时时间（秒） |
| `daemon` | `bool` | 是否为守护线程（设为 `False`） |

> ⚠️ 注：虽然设置了 `setDaemon(False)`，但实际默认行为是主线程退出后不会强制终止这些线程，需手动调用 `wait_for_complete()` 保证清理。

#### 方法

##### `__init__(self, rqueue, timeout=1)`
初始化工作线程。

- **参数**：
  - `rqueue` (`Queue`)：任务队列对象。
  - `timeout` (`float`, 默认 `1`)：从队列取任务的阻塞超时时间。

自动启动线程（调用 `.start()`）。

##### `run(self)`
线程主循环逻辑：

1. 循环尝试从 `r_queue` 中取出任务（格式为 `[callable, args, kw]`）。
2. 若取到的任务中 `callable` 为 `None`，则视为停止信号，线程退出。
3. 否则执行 `callable(*args, **kw)`。
4. 队列为空时捕获 `Empty` 异常，并休眠 1 秒后继续尝试。

> 🛑 当前线程在 `Empty` 异常时使用 `time.sleep(1)`，可能导致最多 1 秒延迟响应新任务或退出信号。

##### `resulthandler(self, rez)`
预留方法，用于处理任务返回结果。当前为空实现，用户可子类化重写此方法以实现回调功能。

> ✅ 扩展建议：若需结果收集，可在 `add_job` 时传入 `result_callback` 并在此方法中触发。

---

### 2.2 `ThreadWorkers` 类

管理多个 `Worker` 实例的线程池控制器。

#### 属性
| 属性 | 类型 | 描述 |
|------|------|------|
| `workQueue` | `Queue` | 存放待处理任务的队列 |
| `worker_cnt` | `int` | 工作线程数量 |
| `workers` | `list[Worker]` | 所有工作线程的列表 |

#### 方法

##### `__init__(self, num_workers=20)`
构造函数，创建指定数量的工作线程。

- **参数**：
  - `num_workers` (`int`, 默认 `20`)：线程池大小。

内部调用 `__createThreadPool(num_workers)` 创建线程。

##### `__createThreadPool(self, num)`
私有方法，创建 `num` 个 `Worker` 实例并加入 `self.workers` 列表。

- **参数**：
  - `num` (`int`)：要创建的线程数。

每个线程共享同一个 `workQueue`。

##### `add_job(self, callable, args=[], kw={})`
向任务队列添加一个任务。

- **参数**：
  - `callable` (`callable`)：可调用对象（函数等）。若为 `None`，表示停止信号。
  - `args` (`list`)：位置参数列表。
  - `kw` (`dict`)：关键字参数字典。

> 💡 示例：`tw.add_job(print, ['Hello'], {'end': '!\\n'})`

任务以 `[callable, args, kw]` 形式放入队列。

##### `wait_for_complete(self)`
等待所有任务执行完毕并回收线程资源。

操作流程：
1. 向队列发送 `worker_cnt` 个 `None` 任务（作为每个线程的退出信号）。
2. 遍历 `workers` 列表，逐个调用 `join()` 等待其结束。
3. 清空 `workers` 列表。

> ✅ 必须调用此方法确保所有线程正常退出，防止程序挂起。

---

## 3. 使用示例

以下是一个使用 `requests` 发起大量 HTTP 请求的示例：

```python
import requests
from thread_worker import ThreadWorkers  # 假设保存为 thread_worker.py

def get(url):
    x = requests.get(url)
    print(x.status_code)

# 创建线程池（默认20个线程）
tw = ThreadWorkers()

# 添加10000个任务
for i in range(10000):
    tw.add_job(get, ['http://www.baidu.com'])

# 等待所有任务完成
tw.wait_for_complete()
print('finished')
```

输出示例：
```
200
200
...
finished
```

---

## 4. API 参考

| 函数/类 | 签名 | 说明 |
|--------|------|------|
| `Worker` | `Worker(rqueue: Queue, timeout: float = 1)` | 工作线程，自动启动 |
| `Worker.run()` | `-> None` | 主循环，处理任务或退出 |
| `Worker.resulthandler(rez)` | `(rez: Any) -> None` | 预留结果处理器 |
| `ThreadWorkers` | `ThreadWorkers(num_workers: int = 20)` | 初始化线程池 |
| `ThreadWorkers.add_job()` | `(callable, args: list = [], kw: dict = {})` | 添加任务 |
| `ThreadWorkers.wait_for_complete()` | `() -> None` | 发送退出信号并等待所有线程结束 |

---

## 5. 注意事项与限制

⚠️ **已知问题与改进建议**：

1. **缺少 `import time`**
   - 在 `Worker.run()` 中使用了 `time.sleep(1)`，但未导入 `time` 模块。
   - ❌ 错误：运行时报 `NameError: name 'time' is not defined`
   - ✅ 修复：在文件顶部添加 `import time`

2. **任务结果无法获取**
   - 当前设计不支持任务返回值的传递。
   - ✅ 建议扩展：可通过 `concurrent.futures.Future` 或回调函数机制增强。

3. **高延迟响应**
   - `get(timeout=self.timeout)` + `except Empty: sleep(1)` 导致最大延迟达 `timeout + 1` 秒。
   - ✅ 建议：将 `sleep(1)` 改为更小值或移除，直接依赖 `get(timeout)` 轮询。

4. **不可复用线程池**
   - 调用 `wait_for_complete()` 后线程已退出，不能再次提交任务。
   - ✅ 如需复用，应重新设计“动态增减线程”或“重启线程池”机制。

5. **异常未捕获**
   - 任务执行过程中抛出异常会中断线程。
   - ✅ 建议在外层加 `try-except` 包裹 `callable(*args,**kw)` 并记录错误。

6. **线程安全**
   - `Queue` 是线程安全的，整体结构合理。
   - 不推荐手动修改 `workers` 或 `workQueue`。

---

## 6. 依赖项

- Python 3.6+
- 标准库：
  - `sys`
  - `threading`
  - `queue`
  - `time`（需显式导入，原代码遗漏）

可选第三方库（仅示例使用）：
- `requests`：用于演示网络请求任务

---

## 附录：修复后的完整代码（建议版本）

```python
import sys
import threading
import time  # 缺失的导入
from threading import Thread
from queue import Queue, Empty


class Worker(Thread):
    def __init__(self, rqueue, timeout=1):
        Thread.__init__(self)
        self.timeout = timeout
        self.setDaemon(False)  # 主线程结束后是否强制退出
        self.r_queue = rqueue
        self.start()

    def run(self):
        while True:
            try:
                task = self.r_queue.get(timeout=self.timeout)
                if task is None or task[0] is None:
                    break
                callable_func, args, kw = task
                try:
                    result = callable_func(*args, **kw)
                    self.resulthandler(result)
                except Exception as e:
                    print(f"Task error: {e}", file=sys.stderr)
            except Empty:
                continue  # 继续轮询，无需额外 sleep

    def resulthandler(self, rez):
        pass


class ThreadWorkers:
    def __init__(self, num_workers=20):
        self.workQueue = Queue()
        self.worker_cnt = num_workers
        self.workers = []
        self.__createThreadPool(num_workers)

    def __createThreadPool(self, num):
        for _ in range(num):
            thread = Worker(self.workQueue)
            self.workers.append(thread)

    def wait_for_complete(self):
        for _ in range(self.worker_cnt):
            self.workQueue.put([None, None, None])  # 发送退出信号

        while self.workers:
            worker = self.workers.pop()
            if worker.is_alive():
                worker.join()

    def add_job(self, callable_func, args=None, kw=None):
        if args is None:
            args = []
        if kw is None:
            kw = {}
        self.workQueue.put([callable_func, args, kw])


if __name__ == '__main__':
    import requests

    def get(url):
        x = requests.get(url)
        print(x.status_code)

    tw = ThreadWorkers(num_workers=10)
    for i in range(100):
        tw.add_job(get, ['http://www.baidu.com'])
    tw.wait_for_complete()
    print('finished')
```

> ✅ 此版本修复了 `time` 导入缺失、异常处理、延迟优化等问题，更具健壮性。