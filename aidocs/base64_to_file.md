# 技术文档：Base64 与 Hex 编码处理工具

---

## 概述

该模块提供了一系列用于处理 Base64 编码和十六进制（Hex）字符串的实用函数，主要用于：

- 将十六进制字符串转换为带 MIME 类型的 Base64 Data URL；
- 从 Base64 Data URL 中提取文件名；
- 将 Base64 编码的数据保存为本地文件。

适用于图像、音频、视频等二进制资源在 Web 应用中的编码与解码场景。

---

## 导入依赖

```python
import os
import re
import base64
from appPublic.uniqueID import getID
```

> `appPublic.uniqueID.getID` 用于生成唯一文件名 ID。

---

## MIME 类型映射表：`MIME_EXT`

一个字典结构，将常见的 MIME 类型映射到对应的文件扩展名。

### 定义

```python
MIME_EXT = {
    # 图片类型
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/bmp": "bmp",
    "image/svg+xml": "svg",
    "image/x-icon": "ico",
    "image/tiff": "tiff",

    # 音频类型
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/ogg": "ogg",
    "audio/webm": "weba",
    "audio/aac": "aac",
    "audio/flac": "flac",
    "audio/mp4": "m4a",
    "audio/3gpp": "3gp",

    # 视频类型
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/ogg": "ogv",
    "video/x-msvideo": "avi",
    "video/quicktime": "mov",
    "video/x-matroska": "mkv",
    "video/3gpp": "3gp",
    "video/x-flv": "flv",
}
```

### 说明

- 用于根据 MIME 类型推断文件扩展名。
- 若未匹配到已知类型，则使用 MIME 的子类型部分作为扩展名（如 `application/pdf` → `.pdf`）。

---

## 函数文档

---

### `hex2base64(hex_str, typ)`

将十六进制字符串转换为带有指定 MIME 类型的 Base64 Data URL 字符串。

#### 参数

| 参数      | 类型   | 描述 |
|-----------|--------|------|
| `hex_str` | `str`  | 输入的十六进制字符串，可选包含 `0x` 或 `0X` 前缀。 |
| `typ`     | `str`  | 目标文件的扩展名（例如 `"png"`, `"mp3"`），用于查找对应 MIME 类型。 |

#### 返回值

- `str`: 格式为 `data:<mime-type>;base64,<base64-data>` 的 Data URL 字符串。
- 如果未找到匹配的 MIME 类型，则使用扩展名作为类型后缀。

#### 示例

```python
hex_data = "89504E470D0A1A0A..."  # PNG 图像的 hex 数据
data_url = hex2base64(hex_data, "png")
# 输出: data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...
```

#### 实现逻辑

1. 移除 `0x` / `0X` 前缀（如果存在）；
2. 使用 `bytes.fromhex()` 转换为字节流；
3. Base64 编码字节流；
4. 查找 `typ` 对应的 MIME 类型，构造 Data URL。

> ⚠️ 注意：若 `typ` 不在 `MIME_EXT` 中，不会抛出异常，但可能生成不标准的 MIME 类型。

---

### `getFilenameFromBase64(base64String)`

从 Base64 Data URL 中解析出推荐的文件名，基于其 MIME 类型自动添加扩展名。

#### 参数

| 参数             | 类型   | 描述 |
|------------------|--------|------|
| `base64String`   | `str`  | Base64 编码的 Data URL 字符串或纯 Base64 内容。 |

#### 返回值

- `str`: 形如 `<unique_id>.<ext>` 的文件名字符串。
  - `<unique_id>` 来自 `getID()` 生成的唯一标识；
  - `<ext>` 由 MIME 类型决定，若无法解析则尝试从类型中提取子类型。

#### 示例

```python
url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
fname = getFilenameFromBase64(url)
# 输出: abc123def.png

invalid = "invalid_base64_string"
fname = getFilenameFromBase64(invalid)
# 输出: xyz789abc (无扩展名)
```

#### 实现逻辑

1. 使用正则表达式匹配 `data:<mime>;base64,<data>` 格式；
2. 提取 `mime_type`；
3. 在 `MIME_EXT` 中查找对应扩展名，否则取 `/` 后的部分（如 `octet-stream`）；
4. 结合唯一 ID 生成文件名。

> ❗ 不会抛出异常，无效输入返回仅含 ID 的文件名。

---

### `base64_to_file(base64_string, output_path)`

将 Base64 编码的字符串（支持 Data URL 格式）解码并写入指定路径的文件。

#### 参数

| 参数              | 类型   | 描述 |
|-------------------|--------|------|
| `base64_string`   | `str`  | Base64 编码字符串，可带 `data:mime;base64,` 头部。 |
| `output_path`     | `str`  | 输出文件的完整路径（包括文件名）。 |

#### 行为

- 自动检测并移除 Data URL 头部（即第一个逗号前的内容）；
- 解码 Base64 数据为二进制；
- 以二进制写模式 (`wb`) 保存至目标路径。

#### 示例

```python
data_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
base64_to_file(data_url, "/tmp/output.png")
# 结果：在 /tmp/output.png 创建 PNG 文件
```

#### 注意事项

- 不检查目录是否存在，若路径不存在会引发 `FileNotFoundError`；
- 不验证 Base64 是否合法，错误数据可能导致 `base64.b64decode` 抛出异常。

---

## 使用示例

```python
# 示例 1: Hex → Base64 Data URL
hex_input = "0x89504E470D0A1A0A..."  # PNG 的 hex
b64_url = hex2base64(hex_input, "png")
print(b64_url)  # data:image/png;base64,...

# 示例 2: 生成带扩展名的唯一文件名
filename = getFilenameFromBase64(b64_url)
print(filename)  # abc123def.png

# 示例 3: 保存为文件
base64_to_file(b64_url, f"/uploads/{filename}")
```

---

## 异常处理建议

虽然当前代码未显式抛出异常，但在生产环境中建议增加以下保护：

```python
try:
    base64_to_file(data, path)
except Exception as e:
    logger.error(f"Failed to save base64 data: {e}")
```

特别是：
- `base64.b64decode()` 可能因格式错误失败；
- 文件 I/O 操作需处理权限或磁盘空间问题。

---

## 总结

| 功能                     | 函数名                  |
|--------------------------|-------------------------|
| Hex → Base64 Data URL     | `hex2base64()`          |
| Base64 → 推荐文件名       | `getFilenameFromBase64()`|
| Base64 → 本地文件         | `base64_to_file()`      |

本模块适合嵌入 Web 后端服务中，用于处理前端上传的内联资源（如 Canvas 截图、录音等），实现快速落地存储或进一步处理。

--- 

✅ **版本要求**：Python 3.6+  
📦 **依赖项**：`appPublic` 包（提供 `uniqueID.getID`）