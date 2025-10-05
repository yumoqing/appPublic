# `ArgsConvert` 与 `ConditionConvert` 技术文档

> **语言**: Python  
> **编码**: UTF-8  
> **模块路径**: `appPublic.argsconvert`（假设）  
> **功能描述**: 提供字符串模板变量替换和条件性文本块解析的工具类。

---

## 概述

本模块包含两个核心类：

1. **`ArgsConvert`**：用于在字符串、列表或字典中查找并替换特定格式的占位符（如 `%{...}%`），支持表达式求值。
2. **`ConditionConvert`**：用于处理带有开始/结束标记的条件性文本块（如 `$<tag>$...$</tag>$`），根据命名空间中的值决定是否保留内容。

这两个类广泛适用于模板渲染、动态配置生成、条件输出等场景。

---

## 安装依赖

无需外部依赖，仅需标准库及以下内部模块：

- `re`: 正则表达式处理
- `appPublic.dictObject.DictObject`: 可属性访问的字典对象
- `appPublic.registerfunction.rfrun`: 允许在 `eval` 中调用注册函数

---

## 类说明

### 一、`ConvertException`

```python
class ConvertException(Exception):
    pass
```

自定义异常类，用于在转换过程中抛出错误，例如标签不匹配、语法错误等。

---

### 二、`ArgsConvert`

#### 功能
对字符串、列表、字典中的占位符进行变量替换。支持嵌套结构和简单表达式计算。

#### 初始化

```python
def __init__(self, preString, subfixString, coding='utf-8')
```

| 参数 | 类型 | 描述 |
|------|------|------|
| `preString` | str | 占位符前缀，如 `"%{"` |
| `subfixString` | str | 占位符后缀，如 `"}%"` |
| `coding` | str | 编码方式，默认为 `'utf-8'`（未实际使用） |

> ⚠️ 注意：虽然参数名为 `coding`，但当前代码中并未真正用于编码转换。

##### 示例：
```python
AC = ArgsConvert('%{', '}%')
```
表示将形如 `%{var_name}%` 的占位符替换成对应的变量值。

#### 方法

##### 1. `convert(obj, namespace, default='')`

递归地将对象中的占位符替换为命名空间中的值。

- 支持类型：字符串、列表、字典
- 返回新对象，原对象不变

| 参数 | 类型 | 描述 |
|------|------|------|
| `obj` | any | 要转换的对象（str / list / dict） |
| `namespace` | dict | 变量命名空间（提供变量值） |
| `default` | any 或 callable | 若变量不存在时返回的默认值；若为可调用，则传入变量名作为参数 |

**返回值**：转换后的对象

**行为说明**：
- 字符串 → 替换占位符
- 列表 → 遍历每个元素递归转换
- 字典 → 构造 `DictObject` 并递归转换每个值

##### 2. `findAllVariables(src)`

从字符串中提取所有匹配的占位符内的变量名（不含前后缀）

| 参数 | 类型 | 描述 |
|------|------|------|
| `src` | str | 源字符串 |

**返回值**：`list[str]`，变量名列表

##### 3. `getVarName(vs)`

从完整占位符字符串中提取变量表达式（去掉前后缀）

| 参数 | 类型 | 描述 |
|------|------|------|
| `vs` | str | 完整的占位符，如 `%{a + b}%` |

**返回值**：`str`，中间部分，如 `"a + b"`

##### 4. `getVarValue(var, namespace, default)`

获取变量的实际值，优先尝试 `eval(var, namespace)`，失败则 fallback 到 `namespace.get(var)` 或 `default`

| 参数 | 类型 | 描述 |
|------|------|------|
| `var` | str | 表达式或变量名 |
| `namespace` | dict | 命名空间 |
| `default` | any 或 callable | 默认值策略 |

**执行顺序**：
1. 使用 `eval(var, ns)` 计算表达式（安全风险需注意）
2. 失败时尝试 `ns.get(var)`
3. 再失败时：
   - 若 `default` 是 callable，调用 `default(var)`
   - 否则返回 `default`

> ✅ 支持复杂表达式：`%{d['a']+'(rr)'}%`、`%{len(mylist)}%`

##### 5. `convertString(s, namespace, default)`

处理单个字符串中的占位符替换。

**算法逻辑**：
1. 找出所有匹配的占位符
2. 对每个占位符：
   - 提取变量名
   - 获取其值
   - 如果非字符串，转为字符串
   - 用该值替换原占位符
3. 特殊优化：如果整个字符串就是单个占位符（如 `%{a}%`），直接返回值本身（可能非字符串）

---

### 三、`ConditionConvert`

#### 功能
实现基于标签对的条件文本块渲染。只有当标签内变量为真时，才保留其中内容。

支持嵌套结构（通过栈管理），类似简易模板引擎的 `if` 语句。

#### 初始化

```python
def __init__(self, pString='$<', sString='>$', coding='utf-8')
```

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `pString` | str | `'$<'` | 开始标签前缀 |
| `sString` | str | `'>$'` | 结束标签后缀 |
| `coding` | str | `'utf-8'` | 编码设置（未实际使用） |

##### 示例：
```python
cc = ConditionConvert()
```
识别如下格式：
```text
$<cond1>$ ... $</cond1>$
```

#### 方法

##### 1. `convert(obj, namespace)`

递归处理对象中的条件块。

支持：字符串、列表、字典

返回转换后的结果。

##### 2. `getVarName(vs)`

同 `ArgsConvert`，去除前后缀得到变量名。

特别地，若以 `/` 开头表示是闭合标签。

##### 3. `getVarValue(var, namespace)`

尝试用 `eval(var, namespace)` 求值，否则 `.get(var, None)`

##### 4. `convertList(parts, namespace)`

核心方法：处理由正则分割的字符串片段列表，实现条件判断与嵌套控制。

使用 `self.buffer1` 作为标签栈记录开启的标签名。

**逻辑流程**：
- 遍历每个片段：
  - 若不是标签 → 添加到结果
  - 若是开启标签（如 `$<abc>$`）→ 压栈，进入子块
  - 若是关闭标签（如 `$</abc>$`）→ 出栈校验，求值决定是否保留子块内容
- 若最终栈非空 → 抛出 `ConvertException`（标签未闭合）

**返回值**：`(result_str, remaining_list)` —— 已处理的结果和剩余待处理部分

##### 5. `convertUnicode(s, namespace)` 和 `convertString(...)`

分别处理 Unicode 和普通字符串，统一调用 `convertList` 实现。

---

## 使用示例

### 示例 1：`ArgsConvert` 基础用法

```python
ns = {
    'a': 12,
    'b': 'of',
    'c': 'abc',
    '是': 'is',
    'd': {
        'a': 'doc',
        'b': 'gg'
    }
}

AC = ArgsConvert('%{','}%')
s1 = "%{a}% is a number,%{d['b']}% is %{是}% undefined,%{c}% is %{d['a']+'(rr)'}% string"
print(AC.convert(s1, ns))
# 输出: "12 is a number,gg is is undefined,abc is doc(rr) string"
```

#### 复杂结构转换

```python
argdict = {
    'my': ['this is a descrciption %{b}%', 123, 'ereg%{a}%,%{c}%'],
    'b': s1
}
converted = AC.convert(argdict, ns)
# 所有嵌套层级中的 %{...}% 都会被正确替换
```

---

### 示例 2：`ConditionConvert` 条件渲染

```python
cc = ConditionConvert()

s2 = "Begin $<abc>$this is $<ba>$ba = 100 $</ba>$condition out$</abc>$ end"
result = cc.convert(s2, {'ba': 23})
print(result)
# 输出: "Begin this is ba = 100 condition out end"

# 因为 'ba' 存在且非 False/null，所以内容保留
```

#### SQL 模板构建

```python
sql_template = """
select * from RPT_BONDRATINGS
where 1=1
$<rtype>$and ratingtype=${rtype}$$</rtype>$
$<bond>$and bond_id = ${bond}$$</bond>$
"""

result = cc.convert(sql_template, {'bond': '943', 'rtype': '1'})
# 输出:
"""
select * from RPT_BONDRATINGS
where 1=1
and ratingtype=1
and bond_id = 943
"""
```

> 💡 注：`${}` 在此仅为占位符形式，实际仍由 `ArgsConvert` 处理更合适，此处演示结合潜力。

---

## 安全注意事项

⚠️ **严重警告**：  
`getVarValue()` 使用了 `eval()`，存在潜在的安全风险！

- 不应将用户输入直接放入占位符表达式
- 建议限制命名空间权限，避免泄露敏感函数
- 推荐替代方案：使用 `ast.literal_eval` 或自定义表达式解析器

---

## 已知限制

| 项目 | 说明 |
|------|------|
| 编码参数无作用 | `coding` 参数未被实际使用 |
| `eval` 安全问题 | 直接执行任意表达式，需谨慎使用 |
| 标签必须严格匹配 | `<a><b></a></b>` 会报错 |
| 不支持 else 分支 | 仅支持 if-like 结构 |
| 性能 | 每次 split + findall，大文本效率较低 |

---

## 设计建议（改进方向）

| 改进建议 | 说明 |
|--------|------|
| 引入沙箱机制 | 限制 `eval` 可访问的内置函数 |
| 支持更多语法 | 如 `$<not cond>$...$</not>$` |
| 使用 AST 解析代替 `eval` | 更安全地处理表达式 |
| 添加缓存编译正则 | 提升性能 |
| 支持异步命名空间解析 | 更灵活的数据源 |

---

## 总结

| 类名 | 用途 | 适用场景 |
|------|------|-----------|
| `ArgsConvert` | 模板变量替换 | 日志模板、邮件内容、动态配置 |
| `ConditionConvert` | 条件文本渲染 | 动态 SQL、HTML 模板、报告生成 |

两者配合可构建轻量级模板引擎，适合内部系统快速开发。

---

## 附录：正则表达式详解

### `ArgsConvert` 的 `re1`

```python
ps = '\\%\\{'
ss = '\\}\\%'
re1 = ps + r'.*?' + ss  # 非贪婪匹配任意字符
```

匹配：`%{任意内容}%`

> 原注释中更复杂的版本被注释掉，当前使用通配模式。

### `ConditionConvert` 的 `re1`

```python
pS = '\\$\\<'
sS = '\\>\\$'
pattern = '(' + pS + '/?' + '[_a-zA-Z_\\u4e00-\\u9fa5][...]*' + sS + ')'
```

匹配：
- `$<tag_name>$`
- `$</tag_name>$`

标签名支持中文、字母、数字、下划线及常见符号。

---

> 📌 **作者**: Unknown  
> 📅 **最后更新**: 2025年4月5日  
> 📚 **适用版本**: Python 3.x