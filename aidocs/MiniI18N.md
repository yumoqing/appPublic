# `MiniI18N` 国际化模块技术文档

```markdown
# MiniI18N 模块技术文档

## 概述

`MiniI18N` 是一个轻量级的 Python 国际化（i18n）工具，用于实现多语言文本的动态加载与翻译。它支持基于线程的用户语言隔离、自动语言检测、键值对格式的消息文件解析，并通过单例模式确保全局唯一实例。

该模块适用于需要在不同语言环境下运行的小型应用或 Web 后端服务。

---

## 依赖

- Python 标准库：
  - `os`, `re`, `sys`, `codecs`, `threading`, `time`, `locale`
- 第三方模块（来自 `appPublic` 包）：
  - `appPublic.folderUtils._mkdir`
  - `appPublic.Singleton.SingletonDecorator`
  - `appPublic.folderUtils.ProgramPath`

> ⚠️ 注意：需确保 `appPublic` 包已安装并可导入。

---

## 核心功能

- 支持 UTF-8 编码的多语言 `.txt` 文件读取。
- 基于正则表达式解析 `key: value` 形式的消息条目。
- 忽略以 `#` 开头的注释行。
- 线程安全的语言上下文管理（每个线程可设置独立语言）。
- 单例模式保证全局配置一致性。
- 自动清理过期客户端语言状态（默认超时 600 秒）。
- 支持语言别名映射（如 `zh-CN` → `zh`）。

---

## 数据格式说明

### 消息文件结构（`msg.txt`）

位于 `{path}/i18n/{lang}/msg.txt`，每行为：

```
key : value
# 这是注释
hello_world : 你好，世界
welcome : 欢迎使用我们的产品
```

#### 规则：
- 使用 `:` 分隔键和值。
- 可包含空格，但会被去除前后空白。
- 支持特殊字符转义（见下文）。
- `#` 开头的行为注释，将被忽略。

---

## 特殊字符编码机制

由于键值中可能包含冒号 `:` 或换行符等，模块内置了一套简单的转义机制。

### 转义表 (`convert_pairs`)

| 原始字符 | 转义后字符串 |
|--------|-------------|
| `:`    | `\x3A`      |
| `\n`   | `\x0A`      |
| `\r`   | `\x0D`      |
| `\`    | `\\\\`      |

> 示例：`user:name` → 键变为 `user\x3Aname`

### 相关函数

#### `charEncode(s: str) -> str`
对字符串中的特殊字符进行编码。

#### `charDecode(s: str) -> str`
对编码后的字符串进行解码，还原原始内容。

---

## 主要函数与类

### 辅助函数

#### `dictModify(d: dict, md: dict) -> dict`
合并字典 `md` 到 `d` 中，仅当值不为 `None` 时更新。

```python
dictModify({'a': 1}, {'a': None, 'b': 2})  # 返回 {'a': 1, 'b': 2}
```

#### `getTextDictFromLines(lines: list[str]) -> dict`
从文本行列表中提取键值对字典，跳过注释，解析 `key: value` 并自动解码。

#### `getFirstLang(lang: str) -> str`
从逗号分隔的语言列表中返回第一个语言标签。

```python
getFirstLang("zh-CN,zh,en")  # 返回 "zh-CN"
```

---

### 类：`MiniI18N`

使用 `@SingletonDecorator` 装饰，确保全局只有一个实例。

#### 构造方法：`__init__(path, lang=None, coding='utf8')`

| 参数     | 类型   | 描述 |
|---------|--------|------|
| `path`  | str    | 应用根路径，用于查找 `/i18n` 目录 |
| `lang`  | str or None | 默认语言（可选），未指定则使用系统默认语言 |
| `coding`| str    | 文件编码，默认 `'utf8'` |

> 初始化时会自动扫描 `path/i18n/` 下所有子目录作为语言包。

#### 属性

| 属性               | 类型     | 描述 |
|--------------------|----------|------|
| `path`             | str      | 根路径 |
| `curLang`          | str      | 系统默认语言（来自 `locale.getdefaultlocale()`） |
| `coding`           | str      | 文本编码方式 |
| `langTextDict`     | dict     | 存储各语言的翻译字典 `{lang: {key: text}}` |
| `clientLangs`      | dict     | 线程级语言状态 `{thread_id: {'timestamp': t, 'lang': lang}}` |
| `languageMapping`  | dict     | 语言别名映射，如 `{'zh-CN': 'zh'}` |
| `timeout`          | int      | 客户端语言状态过期时间（秒），默认 600 |

---

### 公共方法

#### `setLangMapping(lang: str, path: str)`
设置语言别名映射。

```python
i18n.setLangMapping('zh-CN', 'zh')
```

#### `getLangMapping(lang: str) -> str`
获取实际使用的语言名称（考虑映射规则）。

#### `setTimeout(timeout: int = 600)`
设置客户端语言缓存的超时时间。

#### `delClientLangs()`
清理超过 `timeout` 时间未访问的线程语言状态。

> 通常由内部调用，无需手动触发。

#### `getLangDict(lang: str) -> dict`
获取指定语言的翻译字典（经过映射处理）。

#### `getLangText(msg: str, lang: str = None) -> str`
根据当前或指定语言返回翻译文本。若无翻译，则返回原消息。

#### `setupMiniI18N()`
扫描 `i18n` 目录下的所有语言文件夹，加载 `msg.txt` 内容至内存。

> 调用示例：
>
> ```
> project_root/
> └── i18n/
>     ├── en/
>     │   └── msg.txt
>     ├── zh/
>     │   └── msg.txt
>     └── ja/
>         └── msg.txt
> ```

#### `setCurrentLang(lang: str)`
为当前线程设置语言环境。

```python
i18n.setCurrentLang('zh')
```

#### `getCurrentLang() -> str`
获取当前线程所设语言。

> 若未设置，则抛出异常（要求先调用 `setCurrentLang`）。

---

### 魔术方法：`__call__(self, msg, lang=None)`

使对象可直接调用，实现快捷翻译。

```python
_ = i18n  # 绑定翻译函数
_("Hello")  # 等价于 i18n.getLangText("Hello")
```

> 支持 bytes 输入自动解码。

---

## 工厂函数

### `getI18N(coding='utf8') -> MiniI18N`

创建并返回单例化的 `MiniI18N` 实例，使用当前程序路径作为根路径。

```python
from mymodule import getI18N

i18n = getI18N('utf8')
_ = i18n
print(_("Welcome"))
```

---

## 使用示例

### 1. 准备语言文件

```bash
your_project/
└── i18n/
    ├── en/
    │   └── msg.txt
    └── zh/
        └── msg.txt
```

`zh/msg.txt` 内容：

```
# 中文翻译
greeting : 欢迎
goodbye : 再见
error.network : 网络错误，请重试
```

`en/msg.txt` 内容：

```
greeting : Welcome
goodbye : Goodbye
error.network : Network error, please retry
```

### 2. 加载并使用

```python
from mini_i18n import getI18N

# 获取 i18n 实例
i18n = getI18N()

# 设置当前线程语言
i18n.setCurrentLang('zh')

# 翻译
print(i18n('greeting'))  # 输出：欢迎
print(i18n('goodbye'))   # 输出：再见

# 切换语言
i18n.setCurrentLang('en')
print(i18n('greeting'))  # 输出：Welcome
```

### 3. 使用语言映射

```python
i18n.setLangMapping('zh-CN', 'zh')
i18n.setCurrentLang('zh-CN')  # 实际使用 zh 的翻译
```

---

## 注意事项

1. **线程安全**：每个线程可通过 `setCurrentLang()` 独立设置语言。
2. **性能优化**：所有翻译数据在初始化时一次性加载进内存，避免重复 IO。
3. **超时清理**：长时间未活动的线程语言记录将被清除，防止内存泄漏。
4. **编码要求**：所有 `msg.txt` 文件必须为 UTF-8 编码（或其他指定编码）。
5. **错误处理**：未找到翻译时返回原文，适合开发阶段“降级显示”。

---

## 扩展建议

- 添加 `.json` 或 `.yaml` 格式支持。
- 增加运行时动态添加翻译项的功能。
- 提供缺失翻译日志记录接口（如 `missed_pt` 预留字段）。
- 支持复数形式、占位符替换（如 `%s`, `{name}`）。

---

## 版本信息

- 创建时间：未知
- 最后修改：未知
- 作者：未知
- 许可协议：请参考项目整体 LICENSE

---
```