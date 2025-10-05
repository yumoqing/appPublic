# CSVData 类技术文档

`CSVData` 是一个用于读取和处理 CSV 文件的 Python 类，提供了两种读取模式：一次性加载全部数据（`read()`）和逐行迭代处理（`iterRead()`）。该类支持自定义字段名、跳过标题行和数据起始行，适用于灵活解析各种格式的 CSV 数据。

---

## 📦 模块依赖

```python
import csv
```

> 使用标准库中的 `csv` 模块进行 CSV 文件解析。

---

## 🔧 类定义

### `class CSVData(csvfile, names=None, headline=0, dataline=1)`

#### 参数说明：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `csvfile` | str | 必填 | CSV 文件路径 |
| `names` | list 或 None | `None` | 自定义字段名称列表。若提供，则忽略文件中的标题行 |
| `headline` | int | `0` | 标题行所在的行号（从 0 开始），仅在 `names` 为 `None` 时使用 |
| `dataline` | int | `1` | 实际数据开始的行号（从 0 开始） |

---

## 📚 方法说明

### 1. `__init__(self, csvfile, names=None, headline=0, dataline=1)`
初始化 CSVData 实例，设置文件路径与解析参数。

---

### 2. `read(self) -> list[dict]`
以列表形式返回所有记录，每条记录是一个字典（键为字段名，值为对应列值）。

#### 返回值：
- `list[dict]`: 包含所有数据记录的列表，例如：
  ```python
  [
      {'st_date': '2024-01-01', 'open_price': '100', ...},
      {'st_date': '2024-01-02', 'open_price': '102', ...},
      ...
  ]
  ```

#### 工作流程：
1. 打开 CSV 文件（二进制模式 `'rb'` ⚠️ 存在潜在问题，请见下方【⚠️ 注意事项】）
2. 创建 `csv.reader` 对象
3. 若未指定 `names`，则读取第 `headline` 行作为字段名
4. 从第 `dataline` 行开始逐行构建字典记录并添加到结果列表中
5. 关闭文件并返回数据

> ✅ 适合小到中等规模的数据集。

---

### 3. `iterRead(self)`
以流式方式逐行读取 CSV 文件，并触发事件回调函数。适用于大数据文件，避免内存溢出。

#### 回调机制：
- `onBegin()`: 在开始读取前调用（当前实现为空）
- `onRecord(rec)`: 每处理一行有效数据时调用
- `onFinish()`: 成功完成读取后调用

#### 异常处理：
- 使用 `try-except` 捕获异常，确保文件关闭
- 出现错误时重新抛出异常（但变量作用域有误，请见【⚠️ Bug 提示】）

> ✅ 推荐用于大型 CSV 文件处理。

---

### 4. `onBegin(self)`
钩子方法，在迭代读取开始前被调用。默认为空实现，可由子类重写。

> 当前代码中调用了 `self.onBegin()`，但该方法未定义 —— 应为 `onReadBegin`？请见下方 Bug 分析。

---

### 5. `onRecord(self, rec)`
每读取一条有效记录时调用此方法。

#### 参数：
- `rec` (dict): 当前行数据，形如 `{字段名: 值}`

#### 默认行为：
打印当前记录（`print(rec)`）

> 可继承此类并重写该方法以实现自定义逻辑（如入库、计算等）。

---

### 6. `onFinish(self)`
所有数据读取完成后调用。

#### 默认行为：
打印 `"onFinish() called"`

> 可用于资源清理或结束通知。

---

## 🖥️ 示例用法

```python
if __name__ == '__main__':
    import sys
    cd = CSVData(
        sys.argv[1],
        names=['st_date','open_price','max_price','min_price','close_price','volume','adj_price']
    )
    cd.iterRead()
```

### 说明：
- 从命令行传入 CSV 文件路径
- 使用自定义字段名，不依赖文件头部
- 调用 `iterRead()` 流式输出每一行数据

---

## ⚠️ 注意事项与改进建议

### ❗Bug 与潜在问题

| 问题 | 描述 | 建议修复 |
|------|------|---------|
| 1. `onBegin()` 调用错误 | 代码中调用 `self.onBegin()`，但实际定义的是 `onReadBegin()`，会导致 `AttributeError` | 将 `onReadBegin` 改名为 `onBegin`，或修正调用 |
| 2. 异常捕获语法错误 | `except exception as e:` 中 `exception` 应为 `Exception`（首字母大写） | 改为 `except Exception as e:` |
| 3. 文件打开模式冲突 | `read()` 方法使用 `'rb'` 二进制模式打开文件，但 `csv.reader` 需要文本模式 | 改为 `'r'` 并指定编码（如 `'utf-8'`） |
| 4. `fd.close()` 变量作用域错误 | 在 `except` 块中调用 `fd.close()`，但 `fd` 是实例属性应写作 `self.fd` | 改为 `self.fd.close()` |
| 5. 缺少编码设置 | 未指定字符编码，可能导致中文乱码 | 添加 `encoding='utf-8'` 参数 |

---

### ✅ 推荐修改后的 `iterRead()` 示例：

```python
def iterRead(self):
    self.fd = open(self.csvfile, 'r', encoding='utf-8')
    try:
        reader = csv.reader(self.fd)
        fields = None
        if self.names is not None:
            fields = self.names
        lno = 0
        self.onBegin()  # 确保方法存在
        for l in reader:
            if fields is None and lno == self.headline:
                fields = [f for f in l]
            if lno >= self.dataline:
                rec = {}
                for i in range(len(fields)):
                    rec[fields[i]] = l[i]
                self.onRecord(rec)
            lno += 1
        self.fd.close()
        self.onFinish()
    except Exception as e:
        self.fd.close()
        raise e
```

---

## 🧩 继承与扩展建议

可通过继承 `CSVData` 类来实现更复杂的功能：

```python
class MyCSVProcessor(CSVData):
    def onBegin(self):
        print("开始处理数据...")

    def onRecord(self, rec):
        # 示例：过滤价格大于 100 的记录
        if float(rec['close_price']) > 100:
            print("高价值记录:", rec)

    def onFinish(self):
        print("数据处理完毕！")
```

---

## 📎 总结

| 特性 | 支持情况 |
|------|----------|
| 自定义字段名 | ✅ |
| 跳过标题行 | ✅ |
| 指定数据起始行 | ✅ |
| 全量读取 | ✅ (`read`) |
| 流式读取 | ✅ (`iterRead`) |
| 可扩展性 | ✅（支持回调钩子） |
| 错误处理 | ⚠️ 存在缺陷，需修复 |
| 编码支持 | ❌ 缺失，建议增加 |

---

## 📌 版本建议（改进方向）

1. 增加 `encoding` 参数，默认 `'utf-8'`
2. 修复异常捕获与方法命名
3. 使用上下文管理器 (`with open(...)`) 替代手动关闭文件
4. 添加类型注解提升可读性
5. 支持分隔符参数（如 tab、分号等）

---

📘 **结论**：`CSVData` 是一个结构清晰、易于扩展的 CSV 处理类，稍作修正后可用于生产环境。