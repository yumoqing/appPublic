# 文本句子分割工具技术文档

本模块提供两个核心函数，用于智能地将一段包含中英文混合内容的文本按句子进行分割，同时保留对话部分不被错误切分。适用于自然语言处理、文本预处理等场景。

---

## 📌 模块功能概览

| 函数名 | 功能描述 |
|--------|---------|
| `split_english_sentences(text)` | 分割纯英文文本为句子列表，避免在缩写词处误切分 |
| `split_text_with_dialog_preserved(text)` | 分割中英文混合文本，并完整保留引号内的对话内容 |

---

## ✅ 1. `split_english_sentences(text)`

### 功能说明
该函数用于将英文文本正确分割为独立句子，特别处理了以下常见问题：
- 句子结尾标点后缺少空格（如 `"Hello.World"` → `"Hello. World"`）
- 避免在常见缩写词（如 Dr., U.S.A.）处错误断句
- 支持 `.`, `!`, `?` 作为句子结束符

### 参数
| 参数 | 类型 | 说明 |
|------|------|------|
| `text` | `str` | 待分割的英文文本字符串 |

### 返回值
`List[str]`: 分割后的句子列表，每个元素为一个独立句子（已去除首尾空白）

### 实现逻辑详解

#### 步骤 1：修复紧连句点
```python
text = re.sub(r'([a-zA-Z])\\.([A-Z])', r'\\1. \\2', text)
```
- **目的**：修复形如 `Hello.World` 的情况，在句点后添加空格。
- **正则解释**：
  - `([a-zA-Z])`：匹配前一个字母
  - `\\.`：匹配句点 `.`
  - `([A-Z])`：匹配后一个大写字母（新句子开头）
- 示例：`"It is cold.Today it will snow."` → `"It is cold. Today it will snow."`

#### 步骤 2：保护缩写词中的句点
```python
abbreviations = r"(Mr|Mrs|Ms|Dr|St|Jr|Sr|vs|i\\.e|e\\.g|U\\.S\\.A|U\\.K)\\."
text = re.sub(abbreviations, lambda m: m.group(0).replace('.', '<DOT>'), text)
```
- **目的**：防止在 `Dr.` 或 `U.S.A.` 等缩写处分割。
- 使用 `<DOT>` 临时替换缩写中的句点，避免被当作句子结束。
- 支持的缩写包括：
  - `Mr.`, `Mrs.`, `Ms.`, `Dr.`, `St.`, `Jr.`, `Sr.`, `vs.`
  - `i.e.`, `e.g.`, `U.S.A.`, `U.K.`

#### 步骤 3：正则分割句子
```python
sentences = re.split(r'(?<=[.!?])\\s+', text.strip())
```
- 利用**正向后视断言** `(?<=...)` 在 `.`, `!`, `?` 后面的空白处分割。
- 确保只在句子结束符后的空格处分割，而非所有空格。

#### 步骤 4：还原缩写中的句点
```python
sentences = [s.replace('<DOT>', '.') for s in sentences if s.strip()]
```
- 将之前替换成 `<DOT>` 的句点恢复为正常句点。
- 过滤掉空字符串或仅空白的内容。

### 示例调用
```python
text = "Dr. Smith went to the U.S.A. He said, 'Hello world!' How are you?"
result = split_english_sentences(text)
print(result)
# 输出:
# ['Dr. Smith went to the U.S.A.', "He said, 'Hello world!'", 'How are you?']
```

---

## ✅ 2. `split_text_with_dialog_preserved(text)`

### 功能说明
此函数用于处理**中英文混合文本**，并确保双引号或中文引号包裹的对话内容**整体保留**，不会在内部被切断。

> 特别适用于小说、剧本、访谈记录等含大量对话的文本。

### 参数
| 参数 | 类型 | 说明 |
|------|------|------|
| `text` | `str` | 包含中英文和可能对话的原始文本 |

### 返回值
`List[str]`: 分割后的文本片段列表，每项是一个句子或完整的对话块。

### 实现逻辑详解

#### 步骤 1：清理换行与回车
```python
text = ''.join(text.split('\r'))
text = ' '.join(text.split('\n'))
```
- 移除 `\r` 回车符
- 将所有 `\n` 替换为空格，避免跨行断裂影响匹配

#### 步骤 2：定义对话匹配模式
```python
dialog_pattern = r'([“\"](.*?)[”\"])'
```
- 匹配使用中文左/右引号 `“”` 或英文双引号 `""` 包裹的内容
- `(.*?)` 非贪婪捕获中间内容
- `flags=re.DOTALL` 允许匹配跨行对话

#### 步骤 3：逐段提取并处理非对话 + 对话部分
通过 `re.finditer()` 遍历所有对话块：

##### a. 提取当前对话前的非对话文本
```python
non_dialog = text[last_idx:start]
```

##### b. 尝试用中文规则分割（优先中文句末标点）
```python
sentences = re.findall(r'[^。！？!?]*[。！？!?]', non_dialog, re.MULTILINE)
```
- 匹配以 `。`, `！`, `？`, `!`, `?` 结尾的中文/英文句子
- 若无结果，则调用 `split_english_sentences()` 处理纯英文段落

##### c. 添加已分割的句子到结果
```python
parts.extend([s.strip() for s in sentences if s.strip()])
```

##### d. 完整保留整个对话块（不分割）
```python
parts.append(match.group(1).strip())  # 如：“你好！”
```

##### e. 更新索引位置
```python
last_idx = end  # 下一次从对话结束后开始
```

#### 步骤 4：处理最后一个对话之后的剩余文本
重复上述非对话处理流程，完成收尾。

### 示例调用
```python
text = '''
张三说：“你今天过得怎么样？”
李四回答：“还不错！我刚从U.S.A回来。”
然后他笑了笑。
'''

result = split_text_with_dialog_preserved(text)
for i, part in enumerate(result):
    print(f"{i+1}. {part}")
```

### 输出示例
```
1. 张三说：“你今天过得怎么样？”
2. “还不错！我刚从U.S.A回来。”
3. 然后他笑了笑。
```

> 注意：对话内容作为一个整体保留，其中 `U.S.A` 不会被错误切开。

---

## ⚠️ 注意事项与限制

| 项目 | 说明 |
|------|------|
| **缩写支持有限** | 当前硬编码了常用缩写，若需扩展可修改 `abbreviations` 正则 |
| **仅支持双引号对话** | 单引号（如 `'hello'`）不会被视为对话块 |
| **不支持嵌套引号** | 如 `“他说：‘你好’”` 可能导致匹配异常 |
| **性能建议** | 对超长文本建议分段处理，避免正则效率下降 |

---

## 🧪 测试建议

推荐对以下类型文本进行测试验证：
- 含缩写的英文句子（如 `Dr. John works in the U.S.A.`）
- 中英混合带对话（如 `小明说：“I'm fine!”`）
- 多行对话结构
- 特殊符号与标点组合

---

## 📦 总结

本工具包提供了稳健的句子分割能力，尤其适合需要保留语义完整性（特别是对话）的 NLP 前处理任务。结合正则表达式与临时标记机制，有效解决了缩写误切与对话破坏的问题。

> ✅ 推荐用于：文本清洗、对话系统预处理、文学作品分析等场景。

--- 

📌 **作者**: 开发者  
📅 **最后更新**: 2025年4月5日