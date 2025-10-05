# ExcelData 模块技术文档

## 简介

`ExcelData` 是一个基于 `xlrd` 的 Python 工具类，用于从 Excel 文件（`.xls` 或 `.xlsx`）中读取结构化数据，并将其转换为 Python 字典或列表结构。支持类型转换、嵌套结构解析、注释跳过、跨文件引用（include）等功能，适用于配置文件、数据导入等场景。

该模块特别适合将 Excel 表格用作轻量级数据库或配置管理工具。

---

## 依赖

- `xlrd`：用于读取 Excel 文件
- `datetime`：处理日期类型单元格
- `os`, `sys`：系统相关操作
- `appPublic.strUtils.lrtrim`：字符串去首尾空白（需确保此模块存在）

> ⚠️ 注意：`appPublic.strUtils` 是外部自定义模块，必须在项目路径中可用。

---

## 核心功能

- 自动识别并跳过注释行（以 `#` 开头）
- 支持多种数据结构标记（如 `__dict__`, `__list__`, `__include__`）
- 支持字段类型自动转换（`int`, `float`, `str`, `list`）
- 支持多表加载与嵌套结构解析
- 支持跨 Excel 文件包含（include）
- 可扩展性强，便于集成到其他系统中

---

## 全局变量说明

### `TCS` 类型映射表

```python
TCS = {
    'int': int,
    'float': float,
    'str': str,
}
```

用于定义支持的类型转换标识符及其对应的 Python 类型。

---

## 辅助函数

### `isEmptyCell(cell) → bool`

判断某个单元格是否为空。

**参数：**
- `cell`: xlrd 单元格对象

**返回值：**
- `True` 如果是空单元格，否则 `False`

---

### `isCommentValue(v) → bool`

判断某值是否为注释（即字符串且以 `#` 开头）。

**参数：**
- `v`: 任意值

**返回值：**
- `True` 如果是注释，否则 `False`

---

### `purekey(k) → str`

提取键名中的实际名称，去除冒号后的类型/指令信息。

例如：
```python
purekey("name:int")  # 返回 "name"
purekey("age")       # 返回 "age"
```

**参数：**
- `k` (str): 原始键名

**返回值：**
- 不含类型修饰的纯键名

---

### `castedValue(v, k) → any`

根据键名中的类型标识对值进行类型转换或结构处理。

**参数：**
- `v`: 待处理的值
- `k`: 键名（可能包含类型信息，如 `:int`, `:list`）

**支持的操作：**
- `:int`, `:float`, `:str`：执行相应类型转换
- `:list`：将字符串按逗号分割，或包装非列表为列表
- 多重标签支持（如 `key:list:int` 表示转为整数列表）

**返回值：**
- 转换后的值

**示例：**

| 输入 (`v`, `k`) | 输出 |
|------------------|------|
| `"123"`, `"age:int"` | `123` (int) |
| `"1.5,2.7"`, `"values:list:float"` | `[1.5, 2.7]` |
| `42`, `"tags:list"` | `[42]` |

---

## 主要类：`ExcelData`

### 构造函数 `__init__(xlsfile, encoding='UTF8', startrow=0, startcol=0)`

初始化 Excel 数据读取器。

**参数：**
- `xlsfile` (str): Excel 文件路径
- `encoding` (str): 文本编码，默认 `'UTF8'`
- `startrow` (int): 起始行索引（未使用，固定为 0）
- `startcol` (int): 起始列索引（未使用，固定为 0）

**行为：**
- 打开 Excel 文件
- 调用 `dataload()` 加载所有工作表数据
- 存储于 `self._dataset`

---

### 属性与方法

#### `cellvalue(sheet, x, y) → any`

获取指定位置单元格的值，并做必要处理。

**参数：**
- `sheet`: xlrd sheet 对象
- `x`, `y`: 行列索引（从 0 开始）

**返回值：**
- `None`：空单元格
- `datetime.date`：日期类型
- 处理过的字符串（去空格、编码转换）

---

#### `isCommentCell(cell) → bool`

判断单元格是否为注释。

**逻辑：**
- 非空
- 内容是字符串且以 `#` 开头

---

#### `dateMode() → int`

返回 Excel 的日期模式（`0` 表示 1900 基准，`1` 表示 1904 基准），由 `xlrd` 提供。

---

#### `trimedValue(v) → any`

对值进行清理：
- 统一编码为指定格式（默认 UTF-8）
- 使用 `lrtrim` 去除首尾空白字符

---

#### `dataload() → dict`

加载整个 Excel 文件的所有工作表。

**返回值：**
- 字典，键为工作表名（已 trim），值为调用 `loadSheetData(sheet)` 的结果

---

#### `findDataRange(sheet, pos, maxr) → int`

查找当前数据块的最大有效行号。

**用途：**
- 在字典结构中确定子结构边界

**参数：**
- `sheet`: 当前工作表
- `pos`: 起始坐标 `(x, y)`
- `maxr`: 最大行限制

**返回值：**
- 第一个非空行的行号（向下扫描），用于分段解析

---

#### `loadSheetData(sheet) → any`

加载单个工作表的数据，调用 `loadSheetDataRange(...)`。

---

#### `include(filename, id) → any`

从另一个 Excel 文件中包含数据。

**参数：**
- `filename`: 要包含的 Excel 文件路径
- `id`: 访问路径，形如 `['sheet'][key]`，支持点式访问

**实现方式：**
- 创建新的 `ExcelData` 实例
- 使用 `exec` 动态求值表达式 `data[id]`

⚠️ **注意：** 使用了 `exec`，存在安全风险，请仅用于可信文件！

---

#### `loadSingleData(sheet, pos) → any`

加载单个值或一行多个值。

**行为：**
- 若只有一列，则返回单一值
- 否则逐列读取直到遇到空或注释
- 特殊处理 `__include__` 指令

---

#### `loadDictData(sheet, pos, maxr) → dict`

以字典形式加载数据块。

**规则：**
- 每行第一列为 key（支持类型标注）
- value 从下一列开始加载
- 支持 `records:list` 标记加载记录集
- 支持递归结构

---

#### `loadSheetDataRange(sheet, pos, maxr) → any`

核心调度函数，根据首单元格内容决定如何解析数据。

**特殊关键字识别：**
| 关键字 | 含义 |
|--------|------|
| `__dict__` | 解析为字典或字典列表（支持嵌套） |
| `__list__` | 解析为列表（每行一个元素） |
| `__include__` | 包含外部文件数据 |
| 注释或空 | 忽略并继续 |

---

#### `loadRecords(sheet, pos, maxr) → list[dict]`

将表格解析为记录列表（类似 CSV）。

**流程：**
- 第一行作为字段名（可带类型）
- 后续每行为一条记录
- 忽略空列和注释列
- 使用 `castedValue` 进行类型转换

**返回值：**
- 列表，每个元素是一个字段名→值的字典

---

#### `dict() → dict`

返回已加载的全部数据。

---

## 扩展类：`ExcelDataL(ExcelData)`

继承自 `ExcelData`，区别在于 `dataload()` 方法：

- 不是以表名为键的字典
- 而是返回一个列表，每个元素是一个 `{表名: 数据}` 字典

**用途：**
- 保持工作表顺序
- 支持同名表（虽然不推荐）

---

## 使用示例

### 示例 Excel 结构

| A         | B           | C        |
|-----------|-------------|----------|
| name:str  | age:int     | tags:list|
| Alice     | 25          | py,dev   |
| Bob       | 30          | js,web   |

调用后得到：
```python
{
  "Sheet1": [
    {"name": "Alice", "age": 25, "tags": ["py", "dev"]},
    {"name": "Bob", "age": 30, "tags": ["js", "web"]}
  ]
}
```

### 包含外部文件

| A             | B               | C           |
|---------------|------------------|-------------|
| __include__   | config.xlsx     | ['db']['host'] |

会尝试加载 `config.xlsx` 并提取 `data['db']['host']`

---

## 命令行运行

```bash
python exceldata.py your_file.xls
```

输出整个解析结果的 JSON 形式（通过 `print(ed.dict())`）。

---

## 注意事项

1. **编码问题**  
   - 推荐使用 UTF-8 编码保存 Excel 中的文本
   - 若出现乱码，请检查 `encoding` 参数

2. **安全性警告**  
   - `include()` 函数使用 `exec`，不要用于不可信输入

3. **版本兼容性**  
   - 使用 `xlrd`，注意其对 `.xlsx` 的支持有限（建议使用 `xlrd>=1.2.0` 或考虑迁移到 `openpyxl`）

4. **性能**  
   - 适合中小规模配置文件，不适合大数据量导入

5. **错误处理**  
   - 部分异常被捕获并打印，但不会中断程序

---

## 已知限制

- 仅支持读取，不支持写入
- 日期仅提取年月日，忽略时分秒
- `__dict__` 和 `__list__` 结构需要严格对齐
- `exec` 使用存在安全隐患
- `lrtrim` 来自外部模块，需确保安装

---

## 未来改进建议

1. 替换 `exec` 为更安全的路径访问机制（如 `dpath` 或递归查找）
2. 支持更多数据类型（如布尔、JSON）
3. 添加日志系统代替 `print`
4. 支持 `openpyxl` 以兼容现代 Excel 格式
5. 提供导出为 JSON/YAML 的接口

---

## 版权与许可

© 2025 作者保留所有权利。  
可用于内部项目，禁止商业分发。

--- 

> ✅ 文档更新时间：2025年4月5日