# `Config.py` 技术文档

---

## 概述

`Config.py` 是一个用于加载和管理应用程序配置的 Python 模块，采用单例模式（Singleton）确保全局配置的一致性。该模块通过执行指定的配置文件（如 `conf/config.ini`），动态解析并构建配置对象，支持自定义节点类型和字典式访问。

此模块由 **longtop Co.** 开发，遵循开源许可证（见 LICENSE 文件），最初版本发布于 2009 年。

---

## 元信息

| 项目 | 内容 |
|------|------|
| 文件名 | `Config.py` |
| 版权所有 | © 2009 longtop Co. |
| 许可证 | 参见项目根目录下的 `LICENSE` 文件 |
| 作者 | yumoqing@gmail.com |
| 创建日期 | 2009-02-01 |
| 最后修改日期 | 2009-02-05 |

---

## 依赖项

### 内置模块
- `os`
- `sys`

### 第三方/自定义模块
- `appPublic.ExecFile.ExecFile`：用于安全执行配置脚本。
- `appPublic.dictObject.DictObject`：提供类字典的对象封装。
- `appPublic.Singleton.Singleton`：实现单例模式。
- `zope.interface`：用于接口定义（当前未使用具体接口，但已导入）。
- `folderUtils.ProgramPath`：获取程序运行主路径。

> ⚠️ 注意：以上自定义模块属于内部库，需确保在运行环境中正确安装或路径可导入。

---

## 核心类与函数

### 常量

```python
CONFIG_FILE = 'conf/config.ini'
```

默认配置文件路径，相对于程序主目录。

---

### 类：`Node`

```python
class Node(object):
    pass
```

#### 说明：
最基础的空对象类，用作配置树中节点的基础类型。可用于扩展自定义配置节点行为。

#### 用途：
在配置文件中可通过 `Node()` 实例化一个空白节点，后续添加属性。

---

### 类：`Config`

```python
class Config:
    __metaclass = Singleton

    def __init__(self, configpath=None):
        ...
```

#### 功能描述：
`Config` 类是核心配置管理器，使用单例模式保证整个应用中仅存在一个配置实例。

#### 参数：
- `configpath` (str, optional): 自定义配置文件路径。若为 `None`，则使用默认路径 `ProgramPath()/conf/config.ini`。

#### 初始化流程：
1. 若未传入 `configpath`，则根据 `CONFIG_FILE` 和 `ProgramPath()` 构造完整路径。
2. 使用 `ExecFile` 加载并执行配置文件。
3. 向执行环境注入以下可用类型：
   - `Node`: 可创建结构化节点
   - `DictObject`: 字典式对象
   - `dict`: 别名为 `DictObject`，便于使用 `{}` 风格语法创建对象
4. 执行配置脚本，并捕获结果。

#### 属性：
| 属性 | 类型 | 描述 |
|------|------|------|
| `configfile` | str | 当前加载的配置文件完整路径 |
| `__execfile` | ExecFile | 负责解析和运行配置文件的执行器 |

#### 示例配置文件 (`conf/config.ini`) 内容示例：

```python
# config.ini 示例
database = DictObject(
    host='localhost',
    port=3306,
    username='root',
    password='123456'
)

server = Node()
server.host = '0.0.0.0'
server.port = 8080

users = dict(admin='admin@local', dev='dev@local')
```

上述代码将被解析成可访问的配置对象。

#### 错误处理：
如果 `self.__execfile.run()` 返回 `(False, msg)`，会在控制台打印错误信息 `(r, msg)`。

---

### 函数：`getConfig(path=None)`

```python
def getConfig(path=None):
    conf = Config(path)
    return conf
```

#### 功能：
获取 `Config` 单例实例的便捷函数。

#### 参数：
- `path` (str, optional): 指定配置文件路径，优先级高于默认路径。

#### 返回值：
- `Config` 实例（单例）

#### 使用示例：

```python
from Config import getConfig

config = getConfig()  # 使用默认路径
print(config.database.host)  # 输出: localhost

# 或指定路径
custom_config = getConfig("myconf/custom.ini")
```

---

## 使用说明

### 步骤 1：准备配置文件

创建 `conf/config.ini` 文件（或其他路径），内容如下：

```python
app_name = "MyApplication"
version = "1.0.0"

logging = DictObject(
    level="DEBUG",
    file="logs/app.log"
)

features = dict(
    enable_cache=True,
    max_workers=4
)
```

### 步骤 2：在主程序中加载配置

```python
from Config import getConfig

cfg = getConfig()

print(cfg.app_name)           # MyApplication
print(cfg.logging.level)      # DEBUG
print(cfg.features.enable_cache)  # True
```

---

## 设计特点

| 特性 | 描述 |
|------|------|
| ✅ 单例模式 | 确保配置全局唯一，避免重复加载 |
| ✅ 动态执行 | 支持 `.ini` 文件中编写 Python 表达式 |
| ✅ 结构化数据 | 支持 `DictObject` 和 `Node` 创建嵌套结构 |
| ✅ 可扩展性 | 易于注入新类型或上下文变量 |
| ⚠️ 安全性注意 | `ExecFile` 执行任意代码，应确保配置文件来源可信 |

---

## 注意事项

1. **安全性警告**：由于使用了代码执行机制（`ExecFile`），请确保配置文件不被恶意篡改。
2. **路径问题**：`ProgramPath()` 必须返回正确的程序根路径，否则无法定位 `conf/config.ini`。
3. **异常处理建议**：当前出错仅打印消息，建议增强日志记录或抛出异常。
4. **兼容性**：`__metaclass = Singleton` 为旧式类写法（Python 2 风格），在 Python 3 中应使用元类继承方式。

---

## 未来优化建议

- 将 `__metaclass = Singleton` 改为 Python 3 兼容的元类写法。
- 添加 `get()` 方法以安全访问嵌套键（如 `cfg.get('database.host')`）。
- 支持 JSON/YAML 等更安全的配置格式作为替代选项。
- 引入配置验证机制（如基于 schema）。
- 增加单元测试覆盖。

---

## 版权声明

> 本软件由 longtop Co. 开发，遵循项目 LICENSE 文件中的条款发布。  
> 如需商业合作或技术支持，请联系作者：yumoqing@gmail.com

--- 

📅 文档最后更新：2025-04-05