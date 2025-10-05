# 颜色对比度计算工具技术文档

本模块提供了一组用于计算颜色对比度和评估其是否符合 **WCAG（Web Content Accessibility Guidelines）** 标准的函数。这些函数可用于网页设计、UI 开发等场景中，确保文本与背景之间的可读性和无障碍访问性。

---

## 目录

- [功能概述](#功能概述)
- [函数说明](#函数说明)
  - [`calculate_luminance(rgba)`](#calculate_luminancergba)
  - [`get_contrast_ratio(lumA, lumB)`](#get_contrast_ratioluma-lumb)
  - [`get_color_contrast_ratio(color1, color2)`](#get_color_contrast_ratiocolor1-color2)
  - [`wcag_check(color1, color2, font_size=14)`](#wcag_checkcolor1-color2-font_size14)
- [使用示例](#使用示例)
- [注意事项与已知问题](#注意事项与已知问题)
- [参考标准](#参考标准)

---

## 功能概述

该模块实现了以下核心功能：

1. 计算给定 RGBA 颜色的相对亮度（Luminance）。
2. 计算两种颜色之间的对比度比值。
3. 判断对比度是否满足 WCAG 2.0 的 AA 或 AAA 级别要求，考虑字体大小的影响。

> ⚠️ 当前代码存在多个拼写错误和变量名错误，实际使用前必须修复！

---

## 函数说明

### `calculate_luminance(rgba)`

**功能：**  
计算输入颜色的相对亮度（Relative Luminance），依据 [WCAG 2.0 Suggestion E2](https://www.w3.org/TR/WCAG20-TECHS/G17.html#G17-CalcStep) 中定义的加权公式。

**参数：**
- `rgba` (`tuple`): 表示颜色的四元组 `(R, G, B, A)`，其中 R、G、B 为 0–255 范围内的整数，A（Alpha）可选（不参与计算）。

> ✅ 注意：此函数仅使用 RGB 分量，忽略 Alpha 通道。

**返回值：**
- `float`: 相对亮度值，范围在 `0.0`（黑色）到 `1.0`（白色）之间。

**公式：**
```
L = 0.2126 * R + 0.7152 * G + 0.0722 * B
```
其中 R、G、B 应先归一化为 0–1 范围（即除以 255），并应用伽马校正（sRGB 转线性亮度）。但当前实现未包含归一化与伽马校正步骤，**这是一个严重缺陷！**

> 🔴 **警告：当前实现有误！**
> - 变量名错误：`color` 和 `colr` 混用 → 应统一为 `rgba`
> - 缺少归一化处理（需将 0–255 映射到 0–1）
> - 缺少 sRGB 到线性亮度的转换（非线性响应）

✅ 正确做法应如下：
```python
def srgb_to_linear(c):
    c_norm = c / 255.0
    return c_norm / 12.92 if c_norm <= 0.04045 else ((c_norm + 0.055) / 1.055) ** 2.4

lum = 0.2126 * srgb_to_linear(r) +
      0.7152 * srgb_to_linear(g) +
      0.0722 * srgb_to_linear(b)
```

---

### `get_contrast_ratio(lumA, lumB)`

**功能：**  
根据两个颜色的相对亮度计算它们之间的对比度比值。

**参数：**
- `lumA`, `lumB` (`float`): 两个颜色的相对亮度值（来自 `calculate_luminance` 输出）

**返回值：**
- `float`: 对比率，取值范围通常为 `1:1`（无对比）到 `21:1`（最大对比）

**公式：**
```
contrast = (lighter + 0.05) / (darker + 0.05)
```

> ⚠️ 错误：函数体内使用了未定义的变量 `lumX`，应为 `lumA`

🔴 存在 Bug：
```python
darker = min(lumX, lumB)  # ❌ lumX 未定义
```
✅ 应改为：
```python
darker = min(lumA, lumB)
```

---

### `get_color_contrast_ratio(color1, color2)`

**功能：**  
直接传入两个颜色，自动计算其对比度比值。

**参数：**
- `color1`, `color2`: 合法的颜色元组 `(R, G, B[, A])`

**返回值：**
- `float`: 两颜色间的对比度比值

⚠️ 错误：调用了不存在的函数 `get_contrast_Ratio`（大小写错误）

🔴 原始代码错误：
```python
return get_contrast_Ratio(lum1, lum2)  # ❌ 函数名拼写错误
```
✅ 应为：
```python
return get_contrast_ratio(lum1, lum2)
```

---

### `wcag_check(color1, color2, font_size=14)`

**功能：**  
判断两个颜色组合是否满足 WCAG 的可访问性标准（AA 和 AAA 级别）。

**参数：**
- `color1`, `color2`: 颜色元组 `(R, G, B)`
- `font_size` (`int` or `float`): 字体大小（像素），用于决定对比度阈值

**返回值：**
- `tuple(bool, bool)`: 
  - 第一个布尔值表示是否达到 **AA 级别**
  - 第二个布尔值表示是否达到 **AAA 级别**

**逻辑规则：**

| 字体大小       | AA 标准 | AAA 标准 |
|----------------|---------|---------|
| ≥ 18px 或粗体≥14px | 3.0     | 4.5     |
| < 18px          | 4.5     | 7.0     |

> ⚠️ 实际 WCAG 规则更复杂，涉及“大字号”定义（18pt 正常 / 14pt 粗体 ≈ 24px），此处简化处理。

🔴 当前代码错误：
```python
return ratio >= aa, radio >= aaa  # ❌ 'radio' 是拼写错误
```
✅ 应为：
```python
return ratio >= aa, ratio >= aaa
```

---

## 使用示例

假设我们想检查白色文字 `(255, 255, 255)` 在深蓝背景 `(0, 0, 128)` 上的可读性：

```python
# 示例（需先修复所有 bug 后方可运行）

white = (255, 255, 255)
blue = (0, 0, 128)

aa, aaa = wcag_check(white, blue, font_size=16)
print(f"AA compliant: {aa}")   # True?
print(f"AAA compliant: {aaa}") # False?
```

预期输出（修复后）：
```
AA compliant: True
AAA compliant: False
```

---

## 注意事项与已知问题

📌 **当前代码存在多个致命错误，不能直接使用！**

| 问题 | 描述 | 修复建议 |
|------|------|----------|
| `color` / `colr` / `lumX` 变量名错误 | 引用未定义变量导致运行时异常 | 统一变量名为正确拼写 |
| `get_contrast_Ratio` 大小写错误 | Python 区分大小写，函数不存在 | 改为 `get_contrast_ratio` |
| `radio` 拼写错误 | 导致 NameError | 改为 `ratio` |
| 未归一化 RGB 值 | 输入是 0–255，但公式期望 0–1 | 添加 `/ 255.0` 并应用伽马校正 |
| 缺少伽马校正 | 直接线性计算亮度不准确 | 使用 sRGB → 线性转换函数 |
| 字体大小判断逻辑不完整 | 未考虑粗体情况 | 建议增加 `bold` 参数 |

---

## 推荐修复版本（完整修正版）

```python
def srgb_to_linear(c):
    """Convert sRGB component to linear light."""
    c_norm = c / 255.0
    return c_norm / 12.92 if c_norm <= 0.04045 else ((c_norm + 0.055) / 1.055) ** 2.4

def calculate_luminance(rgba):
    r, g, b = rgba[:3]
    lr = srgb_to_linear(r)
    lg = srgb_to_linear(g)
    lb = srgb_to_linear(b)
    return 0.2126 * lr + 0.7152 * lg + 0.0722 * lb

def get_contrast_ratio(lumA, lumB):
    lighter = max(lumA, lumB)
    darker = min(lumA, lumB)
    return (lighter + 0.05) / (darker + 0.05)

def get_color_contrast_ratio(color1, color2):
    lum1 = calculate_luminance(color1)
    lum2 = calculate_luminance(color2)
    return get_contrast_ratio(lum1, lum2)

def wcag_check(color1, color2, font_size=14, bold=False):
    # 简化判断：>=18px 或 (>=14px 且粗体) 视为“大字号”
    is_large_text = font_size >= 18 or (bold and font_size >= 14)
    
    aa_threshold = 3.0 if is_large_text else 4.5
    aaa_threshold = 4.5 if is_large_text else 7.0

    ratio = get_color_contrast_ratio(color1, color2)
    return ratio >= aa_threshold, ratio >= aaa_threshold
```

---

## 参考标准

- [WCAG 2.0 Guideline 1.4.3: Contrast (Minimum)](https://www.w3.org/TR/UNDERSTANDING-WCAG20/visual-audio-contrast-contrast.html)
- [Understanding Success Criterion 1.4.3 | W3C](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [Relative Luminance Calculation - Wikipedia](https://en.wikipedia.org/wiki/Relative_luminance)

---

## 结语

尽管原始代码意图良好，但由于多处语法和逻辑错误，无法正常工作。本文档不仅描述了其设计目标，还指出了关键问题并提供了可运行的修复方案。建议开发者在实际项目中使用经过验证的库（如 `webcolors`、`tinycss2` 或专用 contrast checker 库），或基于本修复版本进行封装。