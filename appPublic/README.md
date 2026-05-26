# EventDispatcher

生产级异步事件调度器。

## 特性

- 支持普通函数
- 支持 async 协程
- 支持实例方法
- 弱引用自动GC
- 异常隔离
- 超时控制
- 自定义错误处理

---

# 使用示例

```python
import asyncio

from event_dispatcher import EventDispatcher


def on_login(data):
    print(data)


async def main():

    dispatcher = EventDispatcher()

    dispatcher.bind(
        "login",
        on_login
    )

    await dispatcher.dispatch(
        "login",
        {
            "user": "张三"
        }
    )


asyncio.run(main())
```

---

# 项目结构

```text
event_dispatcher_project/
├── event_dispatcher.py
└── README.md
```

