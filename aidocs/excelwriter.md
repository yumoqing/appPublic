# `ExcelWriter` 类技术文档

## 概述

`ExcelWriter` 是一个基于 `xlwt` 库的 Python 工具类，用于将嵌套字典或列表结构的数据写入 Excel 文件（`.xls` 格式）。它支持递归处理复杂数据结构（如字典、列表、记录列表等），并自动展开为可读的表格形式。

该工具适用于导出配置、日志、数据库查询结果或其他结构化数据到 Excel 表格中。

---

## 依赖库

- `xlwt`: 用于创建和写入 `.xls` 文件。
- `appPublic.strUtils.lrtrim`: 自定义字符串去空函数（左右空格去除）。

> 注意：`xlwt` 不支持 `.xlsx` 格式，仅支持旧版 `.xls`。

---

## 类定义

```python
class ExcelWriter:
    def __init__(self, encoding='gb2312'):
        self.encoding = encoding
```

### 构造函数 `__init__`

#### 参数：
- **`encoding`** (str): 输出 Excel 文件的字符编码，默认为 `'gb2312'`。  
  常见可选值包括 `'utf-8'`, `'gbk'` 等，需与系统兼容。

#### 示例：
```python
writer = ExcelWriter(encoding='utf-8')
```

---

## 主要方法

### `write(excelfile, dictdata)`

将字典格式的数据写入指定的 Excel 文件，每个顶级键作为工作表名称。

#### 参数：
- **`excelfile`** (str): 输出文件路径（如 `'output.xls'`）。
- **`dictdata`** (dict): 数据字典，键为工作表名，值为待写入内容（支持 dict/list）。

#### 示例：
```python
data = {
    'Sheet1': ['a', 'b', 'c'],
    'Sheet2': {'key': 'value'}
}
writer.write('output.xls', data)
```

> 此方法会为每个 key 创建一个 sheet，并调用 `writeV()` 写入其值。

---

### `writeV(sheet, x, y, v)`

递归写入任意类型值到工作表的指定位置。

#### 参数：
- **`sheet`**: `xlwt.Worksheet` 对象。
- **`x`**, **`y`** (int): 起始行、列索引（从 0 开始）。
- **`v`**: 待写入的值（支持 str/int/float/list/dict）。

#### 行为逻辑：
| 类型 | 处理方式 |
|------|---------|
| `list` | 调用 `writeList()` |
| `dict` | 调用 `writeDict()` |
| 其他（str/int/float） | 直接写入单元格，若为字符串则先去空格 |

#### 返回值：
返回占用的行数（int）。

---

### `writeDict(sheet, x, y, adict)`

将字典写入工作表，每项占一行，键在左，值在右，支持嵌套。

#### 参数：
- `sheet`: 工作表对象
- `x`, `y`: 起始坐标
- `adict`: 字典对象

#### 输出示例：
```
__dict__
key1     value1
key2     [nested...]
```

#### 返回值：
返回所占行数。

---

### `writeList(sheet, x, y, alist, singlecell=False)`

写入列表数据，根据内容自动判断处理方式。

#### 参数：
- `alist`: 列表数据
- `singlecell`: 是否合并为单个单元格（逗号分隔）

#### 分支逻辑：
1. **如果是记录列表（`isRecords(alist)` 为 True）**  
   → 调用 `writeRecords()` 以表格形式输出。
2. **如果包含字典或嵌套结构**  
   → 多行展开，逐项调用 `writeDict` 或 `writeMultiLineList`。
3. **普通列表**  
   → 横向展开在同一行（列递增），除非 `singlecell=True`。

#### 返回值：
返回占用行数。

---

### `writeRecords(sheet, x, y, alist)`

将“记录列表”（即字典列表）以表格形式写入 Excel。

#### 前提条件：
所有元素必须是字典，且值不能是嵌套复杂结构（不支持 list of dict with nested dicts/lists）。

#### 功能：
- 自动生成表头（字段名）
- 支持字段值为列表时标记为 `fieldname:list`
- 自动对齐列位置

#### 示例输入：
```python
[
    {'name': 'Alice', 'tags': ['dev', 'ml']},
    {'name': 'Bob',   'tags': ['qa']}
]
```

#### 输出效果：
| name  | tags:list      |
|-------|----------------|
| Alice | dev,ml         |
| Bob   | qa             |

#### 返回值：
返回写入的记录条数（行数 -1，不含标题行）。

---

### `createRecordTitle(ws, x, y, title, poss, isList=False)` 和 `writeRecordTitle(ws, x, poss)`

辅助方法，用于管理记录字段的列映射。

- `poss`: 字段名 → 列索引 的字典，`__list__` 子集标记哪些字段是列表。
- `createRecordTitle`: 注册字段名及其列位置。
- `writeRecordTitle`: 在指定行写出表头。

---

### `writeMultiLineList(sheet, x, y, alist)`

将列表纵向写入一列，第一行为 `__list__` 标记。

#### 示例输出：
```
__list__
item1
item2
item3
```

#### 返回值：
返回占用行数。

> ⚠️ Bug 提示：代码中存在拼写错误 `os` 应为 `ox`，应修正为：
```python
return x - ox  # 而非 return x - os
```

---

### `isRecords(alist)`

判断一个列表是否为“记录列表”（即字典列表，且无深层嵌套）。

#### 条件：
- 所有元素是字典
- 字典的值不能是字典或包含复杂类型的列表

#### 返回值：
- `True` if 符合记录格式
- `False` otherwise

---

## 使用示例

```python
from appPublic.strUtils import lrtrim
import xlwt

# 实例化
w = ExcelWriter(encoding='utf-8')

# 准备测试数据
data = {
    'my1': ['23423', '423424', 't334t3', 2332, 'erfverfefew'],
    'my2': [
        {'aaa': 1, 'bbb': 'bbb'},
        {'aaa': 2, 'bbb': 'hello'}
    ],
}

# 写入文件
w.write(r'd:\text.xls', data)
```

### 输出说明：

- **Sheet: my1**  
  单行横向显示列表元素。

- **Sheet: my2**  
  表格形式展示两行记录，表头为 `aaa`, `bbb`。

---

## 已知问题与改进建议

| 问题 | 描述 | 建议修复 |
|------|------|----------|
| ❌ `os` 未定义 | `writeMultiLineList` 中 `return x - os` 错误 | 改为 `return x - ox` |
| ⚠️ 编码限制 | `gb2312` 可能无法显示中文 | 推荐使用 `'utf-8'` 或 `'gbk'` |
| ⚠️ 性能问题 | 多层嵌套递归可能导致性能下降 | 添加深度限制或优化结构遍历 |
| 🔄 单元格覆盖 | 启用了 `cell_overwrite_ok=True`，可能造成意外覆盖 | 明确告知用户风险 |
| 💾 格式限制 | 仅支持 `.xls`，不支持 `.xlsx` | 可考虑升级为 `openpyxl` 或 `pandas` 替代 |

---

## 总结

`ExcelWriter` 提供了一种简洁的方式将 Python 中的嵌套数据结构导出为 Excel 文件，特别适合调试、配置导出、简单报表生成等场景。

尽管存在一定局限性（如格式老旧、潜在 bug），但其设计清晰、易于扩展，是一个实用的小型工具类。

---

## 版权与维护

- **作者**: 未知（来自内部模块 `appPublic`）
- **语言**: Python 2/3 兼容（建议运行于 Python 3.x + `xlwt-future`）
- **用途**: 内部数据导出工具

> 建议后续迁移至 `openpyxl` 或 `pandas.DataFrame.to_excel()` 以获得更好的功能和维护支持。