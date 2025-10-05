# `myImport` 函数技术文档

## 概述

`myImport` 是一个用于动态导入 Python 模块的辅助函数。它允许通过字符串形式的模块路径（如 `"os.path"` 或 `"json.decoder.JSONDecoder"`）导入嵌套模块或子模块，而无需使用多个 `import` 语句。

---

## 函数定义

```python
def myImport(modulename):
    modules = modulename.split('.')
    if len(modules) > 1:
        a = __import__(modules[0])
        return eval('a.' + '.'.join(modules[1:]))
    return __import__(modulename)
```

---

## 参数说明

| 参数名       | 类型   | 说明 |
|--------------|--------|------|
| `modulename` | `str`  | 要导入的模块名称，支持点号分隔的完整路径，例如 `"package.submodule"`。 |

---

## 返回值

- **返回类型**: `module` 对象或指定的子模块/类/函数。
- 如果 `modulename` 是单个模块（如 `"math"`），则返回该模块对象。
- 如果 `modulename` 包含子模块或属性（如 `"os.path"` 或 `"json.JSONDecoder"`），则返回对应的嵌套对象。

---

## 工作原理

1. 将输入的 `modulename` 字符串按 `'.'` 分割成模块路径列表。
2. 若路径长度大于 1：
   - 使用 `__import__` 导入最顶层的模块（例如 `"os"`）。
   - 使用 `eval` 动态访问其子模块或属性（例如 `a.path`）。
3. 若路径长度为 1，则直接使用 `__import__` 导入并返回模块。

> ⚠️ 注意：该函数内部使用了 `eval()`，存在潜在的安全风险，应避免在不可信输入上使用。

---

## 示例用法

### 示例 1：导入标准库模块

```python
os = myImport("os")
print(os.getcwd())
```

### 示例 2：导入子模块

```python
path = myImport("os.path")
print(path.join("a", "b"))
```

### 示例 3：导入类或函数

```python
JSONDecoder = myImport("json.decoder.JSONDecoder")
decoder = JSONDecoder()
```

---

## 注意事项

- ✅ 支持多层模块路径导入。
- ⚠️ 使用 `eval()` 存在安全风险，不建议用于处理用户输入。
- ⚠️ 不会自动处理相对导入或包内导入的上下文问题。
- ✅ 可作为简单的动态导入工具，在可控环境下使用较为方便。

---

## 替代方案（推荐）

Python 标准库提供了更安全、更强大的替代方式：

```python
from importlib import import_module

# 推荐使用 import_module 替代 myImport
module = import_module("os.path")  # 仅导入到 os.path 模块级别
```

对于导入类或函数，可结合 `getattr` 使用：

```python
module = import_module("json.decoder")
cls = getattr(module, "JSONDecoder")
```

---

## 总结

`myImport` 提供了一种简洁的动态导入方式，适用于快速原型开发或简单脚本中。但在生产环境中，建议使用 `importlib.import_module` 配合 `getattr` 实现更安全、清晰的模块导入逻辑。