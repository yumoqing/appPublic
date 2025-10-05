# 数据序列化与反序列化工具函数文档

本模块提供了两个用于保存和加载 Python 对象的便捷函数，利用 `pickle` 模块实现对象的持久化存储。

---

## 1. 函数：`saveData(fn, *args)`

### 功能
将任意数量的 Python 对象序列化并保存到指定文件中。

### 参数
| 参数 | 类型 | 说明 |
|------|------|------|
| `fn` | `str` | 要保存数据的文件路径（字符串形式） |
| `*args` | `任意数量的参数` | 要保存的一个或多个 Python 对象 |

### 实现细节
- 文件以二进制写模式 (`'wb'`) 打开。
- 使用列表推导式依次调用 `pickle.dump()` 将每个传入的对象写入文件。
- 写入完成后自动关闭文件。

> ⚠️ 注意：`pickle.dump()` 的返回值是 `None`，因此列表推导式中的变量 `a` 实际上是一个由 `None` 组成的列表，仅用于触发副作用（即执行 dump 操作），并无实际用途。

### 示例
```python
data1 = {'name': 'Alice', 'age': 30}
data2 = [1, 2, 3, 4]
saveData('my_data.pkl', data1, data2)
```
该代码会将字典 `data1` 和列表 `data2` 序列化后保存到 `my_data.pkl` 文件中。

---

## 2. 函数：`loadData(fn, cnt)`

### 功能
从指定文件中反序列化出指定数量的 Python 对象。

### 参数
| 参数 | 类型 | 说明 |
|------|------|------|
| `fn` | `str` | 包含已保存数据的文件路径 |
| `cnt` | `int` | 预期要读取的对象数量 |

### 返回值
- 成功时：返回一个包含 `cnt` 个反序列化对象的列表。
- 失败时（如文件不存在、损坏或数据不足）：返回一个包含 `cnt` 个 `None` 的列表。

### 实现细节
- 文件以二进制读模式 (`'rb'`) 打开。
- 使用列表推导式调用 `pickle.load()` 连续读取 `cnt` 个对象。
- 正常情况下返回读取到的数据列表。
- 若发生异常（如 `EOFError`, `FileNotFoundError` 等），捕获所有异常并返回初始化为 `None` 的列表。

> ⚠️ 注意：此函数使用宽泛的 `except:` 语句，可能掩盖错误。建议在生产环境中替换为更具体的异常处理。

### 示例
```python
data1, data2 = loadData('my_data.pkl', 2)
print(data1)  # 输出: {'name': 'Alice', 'age': 30}
print(data2)  # 输出: [1, 2, 3, 4]
```

---

## 使用注意事项

1. **安全性**：`pickle` 模块不安全用于加载不受信任的数据，因为它可以执行任意代码。请仅用于可信来源的数据。
2. **文件格式**：保存的文件为二进制格式，不可直接阅读或编辑。
3. **版本兼容性**：不同 Python 版本之间的 `pickle` 协议可能存在兼容性问题。
4. **异常处理**：`loadData` 中的 `try-except` 块过于宽泛，建议根据需要捕获特定异常（如 `EOFError`, `FileNotFoundError`）以便调试。

---

## 完整示例

```python
# 保存数据
user_info = {'username': 'Bob', 'level': 5}
scores = [88, 92, 76]
saveData('game_save.pkl', user_info, scores)

# 加载数据
loaded_user, loaded_scores = loadData('game_save.pkl', 2)
print(loaded_user)    # {'username': 'Bob', 'level': 5}
print(loaded_scores)  # [88, 92, 76]
```

---

✅ **适用场景**：快速原型开发、本地配置/状态保存、小型项目中的简单持久化需求。  
❌ **不推荐用于**：跨平台数据交换、网络传输、高安全性要求环境。