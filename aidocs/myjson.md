# JSON 文件操作工具模块文档

本模块提供了一组用于加载和保存 JSON 数据的便捷函数，支持自定义编码格式，并优先使用高性能的 `ujson` 库（若可用），否则回退到标准库中的 `json` 模块。

---

## 依赖说明

- **`ujson`**（可选）：超快的第三方 JSON 解析库。如果系统中已安装 `ujson`，则会优先导入以提升性能。
- **`json`**（内置）：Python 标准库中的 JSON 模块，作为 `ujson` 不可用时的备用方案。
- **`codecs`**（内置）：用于处理带指定编码的文件读写操作。

> ⚠️ 注意：推荐在生产环境中安装 `ujson` 以获得更好的性能：
>
> ```bash
> pip install ujson
> ```

---

## 函数接口

### `loadf(fn, coding='utf8')`

从指定文件路径加载 JSON 数据。

#### 参数：
| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| `fn` | `str` | —— | JSON 文件路径 |
| `coding` | `str` | `'utf8'` | 文件编码格式，默认为 UTF-8 |

#### 返回值：
- 解码后的 Python 对象（如字典、列表等）

#### 示例：
```python
data = loadf('config.json', 'utf8')
print(data['key'])
```

#### 异常处理：
- 若文件不存在或内容不是合法 JSON，将抛出相应异常（如 `FileNotFoundError`, `JSONDecodeError`）。

---

### `dumpf(obj, fn, coding='utf8')`

将 Python 对象序列化为 JSON 并写入指定文件。

#### 参数：
| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| `obj` | `any` | —— | 可被 JSON 序列化的 Python 对象 |
| `fn` | `str` | —— | 目标文件路径 |
| `coding` | `str` | `'utf8'` | 输出文件编码格式，默认为 UTF-8 |

#### 示例：
```python
data = {'name': 'Alice', 'age': 30}
dumpf(data, 'output.json', 'utf8')
```

#### 注意事项：
- 若目标文件已存在，将被覆盖。
- 确保传入的对象是 JSON 可序列化的（例如不包含 `set`、`function` 等类型）。

---

### 兼容性快捷函数

为了与标准 `json` 模块保持接口一致，本模块导出了以下四个常用方法：

| 函数名 | 功能 | 等价于 |
|--------|------|--------|
| `load` | 从文件对象加载 JSON | `json.load(file_obj)` |
| `dump` | 将对象写入文件对象 | `json.dump(obj, file_obj)` |
| `loads` | 从字符串解析 JSON | `json.loads(json_str)` |
| `dumps` | 将对象转为 JSON 字符串 | `json.dumps(obj)` |

> ✅ 提示：这些函数直接代理到底层使用的 JSON 库（`ujson` 或 `json`），无需额外配置。

#### 示例：
```python
json_str = '{"name": "Bob"}'
data = loads(json_str)

with open('data.json', 'w') as f:
    dump({'x': 1}, f)
```

---

## 使用建议

1. **优先使用 `loadf` / `dumpf`**：当需要直接通过文件路径操作 JSON 时，这两个封装函数更简洁安全。
2. **手动控制文件流时使用 `load` / `dump`**：适用于需要上下文管理或其他高级文件操作场景。
3. **性能敏感场景推荐安装 `ujson`**：可显著提升大文件或高频调用下的序列化/反序列化速度。

---

## 完整示例

```python
# 写入数据
config = {
    "host": "localhost",
    "port": 8080,
    "debug": True
}
dumpf(config, "config.json")

# 读取数据
loaded_config = loadf("config.json")
print(loaded_config["host"])  # 输出: localhost
```

---

## 版本兼容性

- 支持 Python 3.6+
- 跨平台兼容（Windows / Linux / macOS）

---

## 许可证

本代码遵循所在项目的整体许可证（请参考项目根目录 LICENSE 文件）。