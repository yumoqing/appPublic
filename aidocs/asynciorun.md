# 技术文档：异步数据库操作运行器

## 概述

该模块提供了一个通用的异步执行环境，用于初始化数据库连接池并运行异步协程任务。它结合了配置管理、数据库连接池和异步事件循环控制，适用于需要访问数据库的异步 Python 应用程序。

---

## 模块依赖

```python
import asyncio
import sys
from sqlor.dbpools import DBPools
from appPublic.jsonConfig import getConfig
```

### 依赖说明：

- `asyncio`：Python 内置异步编程库，用于事件循环管理。
- `sys`：系统参数访问，用于读取命令行参数。
- `sqlor.dbpools.DBPools`：第三方数据库连接池管理类，根据配置初始化多个数据库连接。
- `appPublic.jsonConfig.getConfig`：自定义配置加载工具，支持从指定路径加载 JSON 配置文件。

---

## 函数定义

### `run(coro)`

启动一个异步应用环境，加载配置、初始化数据库连接池，并运行传入的协程。

#### 参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `coro` | `Coroutine` 或 `async function` | 要执行的异步主函数（不带参数的可调用对象） |

> 示例：`run(main)`，其中 `main` 是一个 `async def main(): ...` 定义的函数。

#### 功能流程

1. **解析工作目录路径**：
   - 默认使用当前目录 `'.'`
   - 若命令行提供了第一个参数（`sys.argv[1]`），则将其作为配置路径

2. **加载配置文件**：
   ```python
   config = getConfig(p, {'workdir': p})
   ```
   - 从路径 `p` 加载 JSON 格式的配置文件
   - 提供默认参数 `{'workdir': p}`，可在配置中引用

3. **初始化数据库连接池**：
   ```python
   DBPools(config.databases)
   ```
   - 使用配置中的 `databases` 字段初始化全局数据库连接池
   - 假设 `config.databases` 是符合 `DBPools` 要求的字典结构

4. **设置并运行异步事件循环**：
   - 创建新的事件循环：`asyncio.new_event_loop()`
   - 设置为当前上下文的事件循环
   - 执行传入的协程：`loop.run_until_complete(coro())`

#### 使用示例

```python
async def main():
    # 示例异步主逻辑
    print("Application started")
    # 可以在此进行数据库查询等异步操作
    await asyncio.sleep(1)
    print("Done")

if __name__ == '__main__':
    run(main)
```

运行方式：

```bash
python app.py ./config/
```

> 将会加载 `./config/` 目录下的配置文件，并启动 `main()` 协程。

---

## 配置文件要求

配置文件应包含以下关键字段：

```json
{
  "databases": {
    "default": {
      "engine": "postgresql",
      "host": "localhost",
      "port": 5432,
      "database": "mydb",
      "username": "user",
      "password": "pass"
    }
  }
}
```

具体结构需符合 `sqlor.dbpools.DBPools` 的初始化要求。

---

## 注意事项

1. **线程安全**：每次调用 `run()` 都会创建新的事件循环，适合单次运行场景。
2. **资源清理**：建议在协程结束前显式关闭数据库连接池（如支持的话）。
3. **错误处理**：本函数未包裹异常处理，建议在 `coro` 内部或外部添加 try-except。
4. **并发模型**：基于 `asyncio`，适用于 I/O 密集型任务，如网络请求、数据库操作。

---

## 版本兼容性

- Python >= 3.7
- 支持 Unix 和 Windows 平台

---

## 总结

`run()` 函数是一个轻量级的异步应用启动器，集成了配置加载与数据库连接池初始化功能，适用于微服务、脚本工具或后台任务等异步应用场景。通过简单的封装，降低了异步程序的启动复杂度。