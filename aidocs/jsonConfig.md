# 技术文档：`json_config.py`

```markdown
# JSON 配置管理模块技术文档

## 概述

本模块提供了一个基于 JSON 文件的配置管理系统，支持从文件或流中加载 JSON 数据，并通过字典对象方式访问。它结合了单例模式、路径解析和模板变量替换功能，适用于应用程序的配置读取与管理。

主要特性：
- 从 JSON 文件或文件对象加载数据
- 支持命名空间（NS）中的变量替换
- 使用 `DictObject` 实现属性式访问
- 全局唯一配置实例（单例模式）
- 跨平台路径处理

---

## 依赖库

### 内置模块
- `os`: 路径和环境操作
- `sys`: 命令行参数访问
- `json`: JSON 序列化/反序列化
- `pathlib.Path`: 现代化路径操作

### 自定义模块（来自 `appPublic` 包）
- `DictObject`: 字典封装为可点号访问的对象
- `SingletonDecorator`: 单例装饰器
- `ProgramPath`: 获取程序运行路径工具
- `ArgsConvert`: 支持 `$[var]$` 格式的字符串模板替换

> ⚠️ 注意：这些类需确保在项目中已正确定义并安装。

---

## 函数说明

### `key2ansi(dict)`
> **功能**：将字典的键由 Unicode 编码为 UTF-8 字节串（目前未生效）

#### 参数
| 参数名 | 类型     | 说明           |
|--------|----------|----------------|
| dict   | `dict`   | 输入字典       |

#### 返回值
- `dict`: 处理后的字典（当前版本实际未执行任何有效转换）

> ❗ 注：该函数存在逻辑问题 —— `return dict` 在函数开头即返回，后续代码不可达。建议移除或修复。

---

## 类说明

### `JsonObject(DictObject)`

> 继承自 `DictObject`，用于从 JSON 源加载数据并构建可属性访问的对象。

#### 构造函数：`__init__(jsonholder, keytype='ansi', NS=None)`

##### 参数
| 参数名      | 类型             | 必选 | 默认值    | 说明 |
|-------------|------------------|------|-----------|------|
| `jsonholder`| `str` 或 `file`  | 是   | -         | JSON 文件路径 或 已打开的文件对象 |
| `keytype`   | `str`            | 否   | `'ansi'`  | 键类型（保留字段，当前无实际作用） |
| `NS`        | `dict`           | 否   | `None`    | 命名空间，用于模板变量替换 |

##### 行为描述
1. 判断 `jsonholder` 类型：
   - 若为字符串，则尝试以文本模式打开该路径对应的文件；
   - 否则视为已打开的文件对象直接使用。
2. 使用 `json.load()` 解析内容。
3. 若发生异常，打印错误信息并重新抛出。
4. 若提供了 `NS`，使用 `ArgsConvert('$[', ']$')` 对结构进行变量替换（如 `$[home]$` → `/Users/name`）。
5. 将原始 `jsonholder` 和 `NS` 存入结果字典中作为元数据。
6. 调用父类 `DictObject.__init__()` 初始化动态属性。

##### 示例
```python
obj = JsonObject("config.json", NS={'home': '/Users/dev'})
print(obj.database_url)  # 访问配置项
```

---

### `JsonConfig(JsonObject)`

> 单例类，继承自 `JsonObject`，保证全局仅存在一个配置实例。

#### 特性
- 使用 `@SingletonDecorator` 装饰，确保多次调用构造函数返回同一实例。
- 通常用于应用级配置共享。

##### 示例
```python
cfg1 = JsonConfig("a.json")
cfg2 = JsonConfig("a.json")
assert cfg1 is cfg2  # True，同一实例
```

---

## 工具函数

### `getConfig(path=None, NS=None) -> JsonConfig`

> 快捷函数，用于获取默认配置文件 (`conf/config.json`) 的单例实例。

#### 参数
| 参数名 | 类型     | 必选 | 默认值 | 说明 |
|--------|----------|------|--------|------|
| `path` | `str`    | 否   | 当前工作目录 | 配置文件所在根路径 |
| `NS`   | `dict`   | 否   | `None` | 扩展命名空间变量 |

#### 行为描述
1. 获取程序运行路径（`ProgramPath()`）。
2. 设置默认命名空间包含：
   - `'home'`: 用户主目录
   - `'workdir'`: 当前工作目录或传入路径
   - `'ProgramPath'`: 程序启动路径
3. 若 `NS` 提供额外变量，则合并到命名空间。
4. 加载 `<path>/conf/config.json` 文件。
5. 返回 `JsonConfig` 单例实例。

#### 返回值
- `JsonConfig`: 配置对象实例，支持属性式访问。

#### 示例
```python
config = getConfig()
print(config.server.port)
```

---

## 使用示例

### 主程序测试代码
```python
if __name__ == '__main__':
    conf = JsonConfig(sys.argv[1])
    conf1 = JsonConfig(sys.argv[1], keytype='ansi')
    print("conf=", dir(conf))
    print("conf1=", dir(conf1))
```

> 运行示例：
```bash
python json_config.py ./test_config.json
```

输出将显示两个配置对象的所有属性列表。

---

## 注意事项

1. **`key2ansi` 函数无效**  
   当前实现中 `return dict` 出现在函数第一行，导致其余代码无法执行。若意图是编码键名为 UTF-8，请删除第一个 `return` 并启用注释代码。

2. **异常处理仅打印路径信息**  
   异常被捕获后打印 `self.__jsonholder__`，但此时 `self` 尚未完全初始化，可能导致属性不存在。建议改为打印 `jsonholder` 变量。

3. **文件关闭安全性**
   - 文件在 `finally` 块中关闭，保障资源释放。
   - 仅当输入为路径字符串时才关闭文件，避免对传入的文件对象误关闭。

4. **模板语法**
   - 使用 `$[var]$` 作为占位符，例如：
     ```json
     {
       "data_dir": "$[home]/myapp/data"
     }
     ```
   - 在 `NS={'home': '/Users/john'}` 下会被替换为 `/Users/john/myapp/data`

---

## 安装要求

确保以下包可用（一般为内部开发包）：
```text
appPublic.dictObject
appPublic.Singleton
appPublic.folderUtils
appPublic.argsConvert
```

可通过 pip 安装私有包或将其加入 PYTHONPATH。

---

## 版本历史

| 日期       | 修改人 | 描述 |
|------------|--------|------|
| 2025-04    | 开发者 | 初始版本发布 |

---
```

> ✅ 文档结束。此 Markdown 可直接集成至项目 Wiki 或生成 HTML/PDF 文档。