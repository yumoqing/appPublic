# `PSharedMemory` 类技术文档

## 概述

`PSharedMemory` 是一个基于 Python `multiprocessing.shared_memory.SharedMemory` 封装的类，用于在多个进程之间安全地共享和传递结构化数据（如字典、列表等）。它通过序列化为 JSON 并写入共享内存的方式实现跨进程通信，并提供线程/进程安全的读写操作。

该类支持创建者模式（创建并初始化共享内存）与连接者模式（仅连接已有共享内存），适用于主从进程或生产者-消费者场景。

---

## 依赖

```python
import json
from time import sleep
from multiprocessing import Manager
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.resource_tracker import unregister
```

> ⚠️ 注意：需要 Python 3.8+ 支持 `shared_memory` 模块。

---

## 类定义

### `class PSharedMemory(name: str, datalen: int, data: Any = None)`

#### 参数说明：

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 共享内存对象的唯一名称（系统级标识符） |
| `datalen` | `int` | 预分配的共享内存大小（字节），必须足够容纳序列化后的数据 |
| `data` | `Any` (可选) | 初始化数据。若提供，则当前进程为“创建者”，负责创建并写入共享内存；否则作为“连接者”读取已存在的共享内存 |

> 💡 提示：`data` 通常为可被 `json.dumps()` 序列化的对象（如 `dict`, `list`, `str`, `int` 等）

---

## 成员属性

| 属性名 | 类型 | 描述 |
|--------|------|------|
| `sm` | `SharedMemory` | 实际的共享内存对象实例 |
| `name` | `str` | 共享内存名称 |
| `datalen` | `int` | 分配的共享内存容量（字节） |
| `lock` | `multiprocessing.Lock` | 多进程访问同步锁，确保写操作原子性 |
| `creator` | `bool` | 标志当前进程是否为共享内存的创建者 |
| `tailstring` | `bytes` (类变量) | 数据结束标记 (`b'#:@#'`)，用于分隔有效数据与垃圾内容 |

---

## 方法说明

### `__init__(self, name, datalen, data=None)`

构造函数，初始化共享内存对象。

#### 行为逻辑：
- 若提供了 `data`：
  - 创建新的共享内存区域。
  - 使用 `Manager().Lock()` 创建互斥锁。
  - 调用 `set(data)` 将数据写入共享内存。
- 否则：
  - 连接到已存在的共享内存。
  - 调用 `unregister(...)` 防止 Python 资源追踪器错误尝试销毁该共享内存（避免 `ResourceWarning`）。

> 🔒 注意：多个连接者可以同时连接同一个共享内存，但只能有一个创建者。

---

### `get(self) -> Any`

从共享内存中读取并反序列化数据。

#### 流程：
1. 从 `self.sm.buf` 读取原始字节。
2. 使用 `split(self.tailstring)[0]` 截取到结束标记前的有效部分。
3. 解码为 UTF-8 字符串。
4. 使用 `json.loads()` 反序列化为 Python 对象。

#### 返回值：
- 原始数据对象（如 `dict`、`list` 等）

#### 异常处理：
- 若数据损坏或非合法 JSON，将抛出 `json.JSONDecodeError`。

---

### `set(self, data)`

将数据写入共享内存（线程/进程安全）。

#### 参数：
- `data`: 可 JSON 序列化的任意对象

#### 流程：
1. 获取内部锁（防止并发写冲突）
2. `json.dumps(data)` → 序列化为字符串
3. 编码为 UTF-8 字节 + 添加尾部标记 `tailstring`
4. 检查总长度是否超过 `datalen`
5. 写入共享内存缓冲区

#### 异常：
- 若序列化后数据长度超过预设 `datalen`，抛出：
  ```python
  Exception(f'SharedMemory allocated size is {self.datalen} set size is {len(b)}')
  ```

> ⚠️ 必须保证 `datalen` 足够大以容纳最大可能的数据量。

---

### `__del__(self)`

析构方法，自动清理共享内存资源。

#### 行为：
- 调用 `self.sm.close()`：关闭当前进程对共享内存的引用。
- 如果是创建者（`self.creator == True`），调用 `self.sm.unlink()`：删除系统中的共享内存对象，释放资源。

> ✅ 自动管理生命周期，避免内存泄漏。

---

## 使用示例

### 示例一：启动创建者进程（写入数据）

运行命令：
```bash
python script.py create
```

代码执行路径：
```python
sm = PSharedMemory('rtgerigreth', datalen=200, data={"aaa": "134902t34gf", "bbb": 36})
sleep(10000)  # 保持共享内存存活
```

作用：创建名为 `'rtgerigreth'` 的共享内存，写入指定数据并持续 10000 秒以便其他进程读取。

---

### 示例二：启动连接者进程（读取数据）

运行命令：
```bash
python script.py
```

代码执行路径：
```python
sm = PSharedMemory('rtgerigreth', datalen=200)
x = sm.get()
print(f'data in shared memory: {x}')
```

输出示例：
```
data in shared memory: {'aaa': '134902t34gf', 'bbb': 36}
```

前提：共享内存 `'rtgerigreth'` 已由另一进程创建并写入数据。

---

## 设计要点与注意事项

### ✅ 优点
- **跨进程共享**：利用操作系统级别的共享内存机制，高效传输数据。
- **类型灵活**：支持任意可 JSON 序列化的数据结构。
- **写安全**：使用 `Lock` 防止并发写入导致数据错乱。
- **自动清理**：创建者负责最终释放共享内存资源。

### ⚠️ 注意事项
1. **共享内存名称需全局唯一且一致**
   - 不同进程必须使用完全相同的 `name` 才能访问同一块内存。

2. **预先估算 `datalen` 容量**
   - 必须大于等于最大可能的 `(json.dumps(data)).encode('utf-8') + tailstring` 的字节长度。
   - 推荐预留一定冗余空间。

3. **避免重复创建**
   - 若共享内存已存在，再以 `create=True` 方式尝试创建会引发异常。
   - 当前设计依赖 `data` 是否传入判断角色，需外部协调好创建顺序。

4. **资源泄露防护**
   - 使用 `unregister(..., 'shared_memory')` 阻止 Python 默认资源追踪器误删已被其他进程使用的共享内存。

5. **不支持动态扩容**
   - 共享内存大小固定，无法扩展。超限写入会抛出异常。

6. **无版本控制或过期机制**
   - 数据一旦写入，除非覆盖或重启，否则长期有效。

---

## 完整测试脚本建议

```python
# writer.py
if __name__ == '__main__':
    import sys
    data = {"timestamp": time.time(), "msg": "Hello from writer"}
    sm = PSharedMemory('my_shared_data', datalen=512, data=data)
    print("Writer: Data written.")
    sleep(30)

# reader.py
if __name__ == '__main__':
    import time
    sm = PSharedMemory('my_shared_data', datalen=512)
    for _ in range(10):
        try:
            x = sm.get()
            print("Reader:", x)
            break
        except Exception as e:
            print("Waiting for data...", str(e))
            time.sleep(1)
```

---

## 总结

`PSharedMemory` 提供了一个简洁、实用的封装，使得在多进程环境中共享结构化数据变得简单可靠。适合用于配置广播、状态共享、轻量级 IPC 场景。

| 特性 | 支持情况 |
|------|----------|
| 跨进程通信 | ✅ |
| JSON 数据支持 | ✅ |
| 写操作加锁 | ✅ |
| 自动资源释放 | ✅ |
| 动态扩容 | ❌ |
| 数据加密/校验 | ❌ |
| 多创建者支持 | ❌（仅单创建者） |

> 📌 推荐在受控环境下使用，确保命名唯一性和容量规划合理。

--- 

*文档版本：v1.0*  
*最后更新：2025年4月5日*