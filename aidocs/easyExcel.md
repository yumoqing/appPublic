# `EasyExcel` 技术文档

```markdown
# EasyExcel - Python Excel 操作工具类

`EasyExcel` 是一个基于 `win32com.client` 的轻量级 Python 工具类，用于简化对 Microsoft Excel 文件的自动化操作。它封装了常用功能如读写单元格、插入图片、复制工作表等，适用于 Windows 环境下与 Excel 应用程序交互。

> ⚠️ **注意**：该模块依赖于 COM 接口，仅支持 Windows 平台，并需要本地安装 Microsoft Excel。

---

## 目录

- [简介](#简介)
- [依赖环境](#依赖环境)
- [类定义](#类定义)
- [方法说明](#方法说明)
  - [`__init__`](#__init__)
  - [`save`](#save)
  - [`setSheetName`](#setsheetname)
  - [`newSheet`](#newsheet)
  - [`close`](#close)
  - [`getCell`](#getcell)
  - [`setCell`](#setcell)
  - [`getRange`](#getrange)
  - [`addPicture`](#addpicture)
  - [`cpSheet`](#cpsheet)
- [使用示例](#使用示例)
- [注意事项](#注意事项)

---

## 简介

`EasyExcel` 类提供了一种简洁的方式访问和操作 Excel 工作簿（`.xls` 或 `.xlsx`），包括打开/创建文件、读取和修改单元格数据、插入图像、复制工作表以及保存和关闭文件。

---

## 依赖环境

- 操作系统：Windows
- Python 包：
  - `pywin32`（通过 `pip install pywin32` 安装）
- 软件依赖：Microsoft Excel 已安装并可正常运行

---

## 类定义

```python
class EasyExcel:
    """
    A utility to make it easier to get at Excel. Remembering
    to save the data is your problem, as is error handling.
    Operates on one workbook at a time.
    """
```

此类在实例化时启动 Excel 应用程序 COM 对象，可加载现有工作簿或新建空白工作簿。

---

## 方法说明

### `__init__(filename=None)`

初始化 `EasyExcel` 实例。

| 参数 | 类型 | 描述 |
|------|------|------|
| `filename` | str 或 None | 要打开的 Excel 文件路径；若为 `None`，则创建新工作簿 |

**行为说明**：
- 若提供 `filename`，尝试打开指定文件。
- 否则创建一个新的空白工作簿。
- 自动创建 `Excel.Application` COM 对象。

**示例**：
```python
xls = EasyExcel("D:\\test.xls")   # 打开已有文件
xls_new = EasyExcel()             # 创建新文件
```

---

### `save(newfilename=None)`

保存当前工作簿。

| 参数 | 类型 | 描述 |
|------|------|------|
| `newfilename` | str 或 None | 新文件路径。如果提供，则另存为该路径；否则执行常规保存 |

**行为说明**：
- 如果传入 `newfilename`，使用 `SaveAs` 保存到新位置，并更新内部文件名。
- 否则调用 `Save()` 进行原地保存。

**示例**：
```python
xls.save()                        # 原路径保存
xls.save("D:\\backup.xls")        # 另存为新路径
```

---

### `setSheetName(sheet, name)`

重命名指定工作表。

| 参数 | 类型 | 描述 |
|------|------|------|
| `sheet` | int / str | 工作表索引（从1开始）或名称 |
| `name` | str | 新的工作表名称 |

**示例**：
```python
xls.setSheetName(1, "Data Sheet")
xls.setSheetName("Sheet1", "Results")
```

---

### `newSheet(sheetName)`

> ❌ 当前为空实现（`pass`），尚未实现添加新工作表的功能。

**建议扩展实现**：
```python
def newSheet(self, sheetName):
    self.xlBook.Worksheets.Add().Name = sheetName
```

---

### `close()`

关闭工作簿并退出 Excel 应用程序，释放资源。

**行为说明**：
- 不自动保存更改（`SaveChanges=0`）。
- 调用 `Quit()` 退出 Excel 进程。
- 删除对 `xlApp` 的引用以确保清理。

> ✅ 推荐在脚本结束前显式调用此方法以避免后台残留 Excel 进程。

**示例**：
```python
xls.close()
```

---

### `getCell(sheet, row, col)`

获取指定单元格的值。

| 参数 | 类型 | 描述 |
|------|------|------|
| `sheet` | int / str | 工作表名称或索引 |
| `row` | int | 行号（从1开始） |
| `col` | int | 列号（从1开始） |

**返回值**：单元格内容（字符串、数字、日期等）

**示例**：
```python
value = xls.getCell("Sheet1", 1, 1)  # 获取 A1 单元格值
```

---

### `setCell(sheet, row, col, value)`

设置指定单元格的值。

| 参数 | 类型 | 描述 |
|------|------|------|
| `sheet` | int / str | 工作表名称或索引 |
| `row` | int | 行号（从1开始） |
| `col` | int | 列号（从1开始） |
| `value` | any | 要写入的值 |

**示例**：
```python
xls.setCell("Sheet1", 1, 1, "Hello World")
```

---

### `getRange(sheet, row1, col1, row2, col2)`

读取矩形区域内的所有单元格值，返回二维元组。

| 参数 | 类型 | 描述 |
|------|------|------|
| `sheet` | int / str | 工作表名称或索引 |
| `row1`, `col1` | int | 起始单元格行列坐标 |
| `row2`, `col2` | int | 结束单元格行列坐标 |

**返回值**：嵌套元组结构 `( (r1c1, r1c2), (r2c1, r2c2) )`

**示例**：
```python
data = xls.getRange("Sheet1", 1, 1, 3, 2)
# 返回类似: (('A1', 'B1'), ('A2', 'B2'), ('A3', 'B3'))
```

---

### `addPicture(sheet, pictureName, Left, Top, Width, Height)`

在指定工作表中插入图片。

| 参数 | 类型 | 描述 |
|------|------|------|
| `sheet` | str/int | 目标工作表 |
| `pictureName` | str | 图片文件完整路径（如 BMP、JPG、PNG） |
| `Left` | float | 图片左上角 X 坐标（像素） |
| `Top` | float | 图片左上角 Y 坐标（像素） |
| `Width` | float | 图片宽度（像素） |
| `Height` | float | 图片高度（像素） |

**示例**：
```python
xls.addPicture('Sheet1', r'C:\screenshot.bmp', 20, 20, 1000, 1000)
```

---

### `cpSheet(before)`

复制第一个工作表（硬编码为 `Worksheets(1)`），并将副本放在指定工作表之前。

> ⚠️ **注意**：参数 `before` 实际未被使用，逻辑固定复制第一个工作表并在其前插入副本。

**建议改进**：
```python
def cpSheet(self, before):
    shts = self.xlBook.Worksheets
    shts(1).Copy(Before=shts(before))
```

**当前行为**：
```python
shts(1).Copy(None, shts(1))  # 在 Sheet1 后面插入副本
```

---

## 使用示例

以下是一个完整的使用案例：

```python
if __name__ == "__main__":
    PNFILE = r'c:\screenshot.bmp'
    xls = EasyExcel(r'D:\test.xls')
    xls.addPicture('Sheet1', PNFILE, 20, 20, 1000, 1000)
    xls.cpSheet('Sheet1')       # 复制第一个工作表
    xls.save()                  # 保存更改
    xls.close()                 # 关闭并释放资源
```

---

## 注意事项

1. **必须手动调用 `save()` 和 `close()`**  
   类不会自动保存或清理资源，请务必在程序结束前调用 `close()` 防止 Excel 进程残留。

2. **错误处理缺失**  
   当前代码未包含异常捕获机制，建议在生产环境中添加 try-except 包裹关键操作。

3. **性能提示**  
   COM 通信较慢，频繁读写单元格会影响性能。建议批量操作使用 `getRange` / `setRange` 方式优化。

4. **线程安全**  
   `win32com.client.Dispatch('Excel.Application')` 不是线程安全的，不建议多线程并发操作。

5. **文件格式兼容性**  
   支持 `.xls` 和 `.xlsx` 格式，但需注意旧版 Excel 可能无法打开新版格式。

---

## 许可与版权

此代码为开源工具片段，可用于学习与项目集成。请遵守 Python 及 Microsoft Excel 相关许可协议。
```