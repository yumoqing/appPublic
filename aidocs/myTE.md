# 模板引擎技术文档

## 简介

`MyTemplateEngine` 是一个基于 [Jinja2](https://jinja.palletsprojects.com/) 的轻量级模板渲染引擎，支持文件和字符串模板的渲染、变量注入、JSON 数据加载以及自定义全局函数。该模块封装了常用的文件路径处理、类型转换、数据访问等功能，适用于配置生成、报告输出、代码模板等场景。

---

## 功能特性

- ✅ 支持从字符串或文件加载模板
- ✅ 支持多路径模板搜索（通过 `pathList`）
- ✅ 内置常用工具函数（如 `json`, `hasattr`, 类型转换等）
- ✅ 提供便捷的 JSON 文件与模板结合渲染功能
- ✅ 自动处理跨平台路径分隔符
- ✅ 可扩展的全局变量/函数注入机制
- ✅ 支持 UTF-8 编码输入输出（可配置）

---

## 安装依赖

```bash
pip install jinja2 ujson apppublic
```

> 注：`appPublic.argsConvert` 和 `appPublic.dictObject` 来自第三方包 `apppublic`，需确保已安装。

---

## 模块导入说明

```python
import os
import sys
try:
    import ujson as json  # 更快的 JSON 解析器
except ImportError:
    import json           # 标准库回退
from jinja2 import Environment, FileSystemLoader, BaseLoader, meta
import codecs
from appPublic.argsConvert import ArgsConvert
from appPublic.dictObject import DictObject
```

---

## 公共函数

### `isNone(obj) -> bool`

判断对象是否为 `None`。

#### 参数：
- `obj`: 任意对象

#### 返回值：
- `True` 如果 `obj` 是 `None`，否则 `False`

---

### `string_template_render(tmp_string: str, data: dict) -> str`

使用字典数据渲染字符串模板。

#### 参数：
- `tmp_string`: Jinja2 风格的模板字符串
- `data`: 渲染所需的数据字典

#### 示例：

```python
result = string_template_render("Hello {{ name }}!", {"name": "Alice"})
# 输出: Hello Alice!
```

---

## 类：`MyTemplateEngine`

主模板引擎类，封装了完整的模板解析与渲染能力。

### 构造函数：`__init__(pathList, file_coding='utf-8', out_coding='utf-8', env={})`

初始化模板引擎实例。

#### 参数：
| 参数名        | 类型             | 说明 |
|---------------|------------------|------|
| `pathList`     | `str` 或 `list` | 模板文件搜索路径列表（支持单个路径或路径列表） |
| `file_coding`  | `str`            | 模板文件读取编码，默认 `'utf-8'` |
| `out_coding`   | `str`            | 输出编码（目前主要用于内部一致性，实际返回为字符串） |
| `env`          | `dict`           | 用户自定义注入到模板中的全局变量或函数 |

#### 初始化行为：
1. 创建 `FileSystemLoader` 加载器，用于从指定路径加载模板。
2. 初始化 `Environment` 并注册内置函数和工具。
3. 向 Jinja2 全局命名空间 (`globals`) 注入以下内容：

| 名称 | 类型 | 用途 |
|------|------|------|
| `json` | module | 提供 `json.dumps/json.loads` |
| `hasattr` | built-in | 判断对象是否有某属性 |
| `int`, `float`, `str`, `type`, `len` | built-in | 基础类型与操作 |
| `isNone` | function | 判断是否为 `None` |
| `render` | method | 调用当前引擎渲染模板文件 |
| `renders` | method | 渲染模板字符串 |
| `ArgsConvert` | class | 参数转换工具类 |
| `renderJsonFile` | method | 快捷方法：用 JSON 文件数据渲染模板 |
| `ospath(x)` | lambda | 统一路径分隔符（适应 Windows/Linux） |
| `basename(x)` | lambda | 获取路径中的文件名部分 |
| `basenameWithoutExt(x)` | lambda | 获取无扩展名的文件名 |
| `extname(x)` | lambda | 获取文件扩展名 |

#### 示例：

```python
te = MyTemplateEngine(['/templates', '/shared'], file_coding='utf-8')
```

---

### 方法：`get_template_variables(tmpl: str) -> list[str]`

分析模板字符串中所有未声明但使用的变量名。

#### 参数：
- `tmpl`: Jinja2 模板字符串

#### 返回值：
- 所有在模板中引用但未定义的变量名列表（可用于调试或预检）

#### 示例：

```python
vars = te.get_template_variables("Hello {{ user.name }}! You have {{ count }} messages.")
# 返回: ['user', 'count']
```

---

### 方法：`set(k: str, v: Any)`

向模板上下文注入全局变量或函数。

#### 参数：
- `k`: 变量名（字符串）
- `v`: 值或可调用对象

> ⚠️ 注意：此操作会影响后续所有模板渲染。

#### 示例：

```python
te.set('site_name', 'MySite')
te.set('now', lambda: datetime.now())
```

---

### 方法：`_render(template: Template, data: dict) -> str`

内部方法：执行模板渲染。

#### 参数：
- `template`: 已加载的 Jinja2 `Template` 对象
- `data`: 数据字典

#### 返回值：
- 渲染后的字符串

---

### 方法：`renders(tmplstring: str, data: dict) -> str`

渲染模板字符串。

#### 参数：
- `tmplstring`: Jinja2 模板字符串
- `data`: 渲染数据

#### 特性：
- 将传入的 `data` 包装成 `global()` 函数注入模板，允许在模板中通过 `global()` 访问原始数据结构。

#### 示例模板：

```jinja2
User: {{ global().user.name }}
Total: {{ len(global().items) }}
```

#### 使用示例：

```python
output = te.renders("Hello {{ name }}!", {"name": "Bob"})
```

---

### 方法：`render(tmplfile: str, data: dict) -> str`

渲染指定路径的模板文件。

#### 参数：
- `tmplfile`: 模板文件相对或绝对路径（将在 `pathList` 中查找）
- `data`: 渲染数据字典

#### 示例：

```python
with open('data.json') as f:
    data = json.load(f)
result = te.render('email_template.html', data)
```

---

### 方法：`renderJsonFile(tmplfile: str, jsonfile: str) -> str`

快捷方法：使用 JSON 文件中的数据渲染模板文件。

#### 参数：
- `tmplfile`: 模板文件路径
- `jsonfile`: JSON 数据文件路径

#### 行为：
1. 读取并解析 `jsonfile`
2. 使用其内容作为上下文调用 `render(tmplfile, data)`

#### 示例：

```python
output = te.renderJsonFile('report.html', 'data.json')
```

---

## 辅助函数：`tmpTml(f: str, ns: dict) -> str`

将模板文件渲染后保存至 `/tmp/` 目录，并返回生成文件的路径。

#### 参数：
- `f`: 模板文件路径
- `ns`: 数据上下文字典

#### 返回值：
- 生成的临时文件完整路径（例如 `/tmp/report.html`）

#### 流程：
1. 创建 `MyTemplateEngine` 实例，搜索路径为当前目录 `.`
2. 读取模板内容
3. 渲染模板
4. 写入 `/tmp/<原文件名>`
5. 返回文件路径

#### 示例：

```python
temp_path = tmpTml('template.txt', {'name': 'Test'})
print(f"Generated at: {temp_path}")
```

---

## 命令行使用

当直接运行此脚本时，支持命令行调用：

```bash
python template_engine.py <template_file> <json_data_file>
```

#### 示例：

```bash
python template_engine.py hello.tmpl.json data.json
```

程序会：
1. 读取模板文件
2. 加载 JSON 数据
3. 渲染并输出结果到标准输出

> 若参数不足，打印用法提示并退出。

---

## 模板语法示例（Jinja2）

```jinja2
<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
  <h1>Welcome, {{ user.name }}!</h1>
  <p>You have {{ len(messages) }} messages.</p>

  {% if not isNone(subtitle) %}
    <h2>{{ subtitle }}</h2>
  {% endif %}

  <p>File: {{ basenameWithoutExt(global().input_file) }} (Ext: {{ extname(global().input_file) }})</p>
</body>
</html>
```

---

## 编码说明

- 所有文件读写均使用 `codecs.open(..., encoding='utf-8')`
- 默认编码可由构造函数设置
- 推荐统一使用 UTF-8 编码避免乱码问题

---

## 错误处理建议

| 异常类型 | 建议措施 |
|--------|---------|
| `TemplateNotFound` | 检查 `pathList` 是否包含目标模板路径 |
| `UnicodeDecodeError` | 确保文件真实编码与 `file_coding` 一致 |
| `JSONDecodeError` | 验证 JSON 文件格式正确 |
| `UndefinedError` | 使用 `get_template_variables()` 检查缺失变量 |

---

## 扩展建议

可通过 `env` 参数或 `set()` 方法添加更多工具函数，例如：

```python
te.set('upper', str.upper)
te.set('today', lambda: datetime.today().strftime('%Y-%m-%d'))
```

也可集成 `DictObject` 实现更灵活的数据访问。

---

## 版权与许可

© 2025 Your Company. 开源项目，请保留原作者信息。

使用遵循 MIT License（除非另有声明）。