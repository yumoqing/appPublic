# 技术文档：文件与路径操作工具库

本项目是一个轻量级的 Python 工具模块，封装了常用的文件系统操作功能，包括临时文件生成、路径处理、目录遍历、文件复制/删除等。适用于跨平台（Windows/Linux/macOS）环境下的文件管理任务。

---

## 目录

- [1. 模块概览](#1-模块概览)
- [2. 依赖说明](#2-依赖说明)
- [3. 函数列表](#3-函数列表)
- [4. 核心函数详解](#4-核心函数详解)
- [5. 使用示例](#5-使用示例)
- [6. 注意事项](#6-注意事项)

---

## 1. 模块概览

该模块提供以下主要功能：

| 功能类别       | 提供的功能 |
|----------------|-----------|
| 路径与目录操作 | `ProgramPath`, `listFolder`, `listFile`, `folderInfo`, `_mkdir`, `rmdir_recursive` |
| 文件操作       | `temp_file`, `_copyfile`, `_copydir` |
| 字符串辅助     | `startsWith`, `endsWith` |
| 时间格式化     | `timestamp2datatiemStr` |
| 随机路径生成   | `filepoolpath` |

> ⚠️ 注：部分 Windows 特定代码（如 `win32api`）已被注释，当前版本为通用跨平台实现。

---

## 2. 依赖说明

### 内置依赖
此模块仅使用 Python 标准库，无需额外安装第三方包：
```python
import os
import sys
import stat
import platform
import time
import random
import tempfile
```

### 可选依赖（已注释）
```python
# import win32api  # 用于获取逻辑驱动器信息（Windows专用），目前未启用
```
> 若需启用驱动器扫描功能，请通过 `pip install pywin32` 安装对应模块并取消注释。

---

## 3. 函数列表

| 函数名 | 描述 |
|--------|------|
| `temp_file(suffix=None, prefix=None, dir=None, text=False)` | 创建一个唯一的临时文件并返回其路径 |
| `filepoolpath(root)` | 基于哈希算法生成分层存储路径，用于避免大量文件集中在同一目录 |
| `startsWith(text, s)` | 判断字符串是否以指定前缀开头 |
| `endsWith(text, s)` | 判断字符串是否以指定后缀结尾 |
| `ProgramPath()` | 获取当前脚本或可执行文件所在目录 |
| `timestamp2datatiemStr(ts)` | 将时间戳转换为标准日期时间字符串格式 |
| `listFolder(path, recursive=False)` | 遍历目录下所有子文件夹（支持递归） |
| `listFile(folder, suffixs=[], recursive=False)` | 遍历目录中符合条件的文件（支持扩展名过滤和递归） |
| `folderInfo(root, uri='')` | 返回指定目录下的文件/文件夹元数据列表 |
| `rmdir_recursive(dir)` | 递归删除目录及其内容 |
| `_mkdir(newdir)` | 安全创建目录（自动创建父级目录，若已存在不报错） |
| `_copyfile(fp, dir)` | 复制文件到目标目录，并解决重名问题 |
| `_copydir(fp, dir, topdistinct)` | 递归复制整个目录结构 |
| `mkdir`, `copyfile`, `copydir`, `rmdir` | 上述函数的别名，便于调用 |

---

## 4. 核心函数详解

### `temp_file(...)`
**用途**：安全地创建一个临时文件并关闭句柄，返回文件路径。

**参数**：
- `suffix` (str): 文件后缀（如 `.tmp`）
- `prefix` (str): 文件名前缀
- `dir` (str): 存放目录；默认为系统临时目录
- `text` (bool): 是否以文本模式打开（实际未使用）

**返回值**：  
`str` - 生成的临时文件完整路径。

**示例**：
```python
fp = temp_file(suffix='.log', prefix='app_', dir='/tmp')
# => /tmp/app_abc123.log
```

---

### `filepoolpath(root)`
**用途**：根据随机数对多个质数取模，构建多层级子目录路径，适合大规模文件分布存储。

**原理**：利用五个质数 `[191, 193, 197, 199, 97]` 对随机值取模，形成五层嵌套目录结构，有效分散 I/O 压力。

**参数**：
- `root` (str): 根目录路径

**返回值**：  
`str` - 如 `/data/100/87/45/23/67`

**应用场景**：  
日志系统、上传服务、缓存池等需要防止单目录文件过多的情况。

---

### `startsWith(text, s)` / `endsWith(text, s)`
**用途**：替代原生 `str.startswith()` 和 `str.endswith()` 的简化版本（兼容性写法）。

**参数**：
- `text` (str): 待检测字符串
- `s` (str): 匹配子串

**返回值**：  
`bool` - 是否匹配成功

---

### `ProgramPath()`
**用途**：获取程序运行时所在的根目录，支持 PyInstaller 打包后的可执行文件。

**行为逻辑**：
- 如果是打包后的 `.exe` 或二进制文件（`sys.frozen == True`），则返回 `sys.executable` 所在目录。
- 否则返回 `sys.argv[0]`（即主脚本）所在目录。

**返回值**：  
`str` - 绝对路径，表示程序运行目录。

---

### `timestamp2datatiemStr(ts)`
**用途**：将 Unix 时间戳转换为可读的时间字符串。

> ❗ 函数名拼写错误：应为 `timestamp2datetimeStr`，但保留原始命名。

**参数**：
- `ts` (int/float): 时间戳

**返回值**：  
`str` - 格式为 `"YYYY-MM-DD HH:MM:SS"` 的时间字符串

**示例输出**：
```
2025-04-05 14:23:01
```

---

### `listFolder(path, recursive=False)`
**用途**：列出指定路径下的所有子目录（可递归）。

**参数**：
- `path` (str): 起始路径
- `recursive` (bool): 是否递归进入子目录

**返回值**：  
生成器对象，逐个返回每个子目录的绝对路径。

**示例**：
```python
for d in listFolder('/home/user', recursive=True):
    print(d)
```

---

### `listFile(folder, suffixs=[], recursive=False)`
**用途**：查找目录中符合扩展名条件的文件。

**参数**：
- `folder` (str): 搜索起始路径
- `suffixs` (list): 扩展名列表（如 `['.txt', '.py']`），忽略大小写
- `recursive` (bool): 是否递归搜索

**返回值**：  
生成器对象，返回匹配文件的绝对路径。

**注意**：
- 若 `suffixs` 为空，则返回所有文件。
- 扩展名建议包含点号（`.`）。

**示例**：
```python
pdfs = list(listFile('/docs', ['.pdf'], recursive=True))
```

---

### `folderInfo(root, uri='')`
**用途**：获取某虚拟路径下的文件/文件夹详细信息列表。

**参数**：
- `root` (str): 实际根目录
- `uri` (str): 虚拟路径（如 `/user/docs`）

**逻辑说明**：
- 支持类似 Web 的 URI 路径解析（如 `/a/b/c` → `root/a/b/c`）
- 自动分割 `/` 并拼接真实路径
- 返回包含类型、大小、修改时间等信息的字典列表

**返回项结构**：
```json
{
  "id": "/user/docs/report.pdf",
  "name": "report.pdf",
  "path": "user/docs",
  "type": "file",
  "size": 10240,
  "mtime": "2025-04-05 14:23:01"
}
```

**适用场景**：  
文件浏览器后端接口、资源管理器 API 数据源。

---

### `rmdir_recursive(dir)`
**用途**：递归删除非空目录。

**特性**：
- 对只读文件先修改权限（加写权限）再删除
- 先删除子项，最后删除自身目录
- 不会抛出“目录非空”异常

**警告**：危险操作，请确保路径正确！

---

### `_mkdir(newdir)`
**用途**：智能创建目录，支持自动创建父级目录。

**特性**：
- 若目录已存在，静默跳过（无异常）
- 若中间路径不存在，则自动补全
- 等价于 `os.makedirs(..., exist_ok=True)`

---

### `_copyfile(fp, dir)`
**用途**：将文件复制到目标目录，并自动处理同名冲突。

**流程**：
1. 读取源文件名
2. 调用 `getFileName(name, dir)` 解决重名（见备注）
3. 分块读取（64KB）进行复制，节省内存
4. 返回布尔值表示是否成功

> ✅ 支持大文件复制

---

### `_copydir(fp, dir, topdistinct)`
**用途**：递归复制整个目录树。

**参数**：
- `fp`: 源目录路径
- `dir`: 目标父目录
- `topdistinct`: 防止顶层重复复制的标记路径

**机制**：
- 在目标目录下创建同名新目录
- 遍历子项：如果是目录则递归复制，否则调用 `_copyfile`
- 忽略 `topdistinct` 层以防循环引用

**别名定义**：
```python
mkdir = _mkdir
copyfile = _copyfile
copydir = _copydir
rmdir = rmdir_recursive
```

---

## 5. 使用示例

### 示例 1：创建临时日志文件
```python
log_path = temp_file(suffix='.log', prefix='myapp_')
with open(log_path, 'w') as f:
    f.write("App started at %s\n" % time.time())
```

### 示例 2：组织海量图片存储路径
```python
storage_root = "/images"
img_path = filepoolpath(storage_root)
os.makedirs(img_path, exist_ok=True)
shutil.move(upload_file, os.path.join(img_path, 'photo.jpg'))
```

### 示例 3：列出所有 Python 文件
```python
for py_file in listFile('/project', suffixs=['.py'], recursive=True):
    print("Found:", py_file)
```

### 示例 4：获取目录信息用于前端展示
```python
info = folderInfo('/data', '/user/docs')
import json
print(json.dumps(info, indent=2))
```

### 示例 5：安全删除缓存目录
```python
cache_dir = os.path.join(ProgramPath(), 'cache')
if os.path.exists(cache_dir):
    rmdir(cache_dir)
```

---

## 6. 注意事项

### ⚠️ 已知问题
1. **函数名拼写错误**：
   ```python
   def timestamp2datatiemStr(ts): ...
   ```
   正确应为 `timestamp2datetimeStr`，请在后续版本中修正。

2. **`getFileName` 函数缺失**：
   在 `_copyfile` 和 `_copydir` 中调用了 `getFileName(name, dir)`，但在代码中未定义。推测是外部依赖或遗漏函数。

   > 🛠️ 建议补充如下实现：
   ```python
   def getFileName(name, directory):
       base_name, ext = os.path.splitext(name)
       counter = 1
       new_name = name
       while os.path.exists(os.path.join(directory, new_name)):
           new_name = f"{base_name}_{counter}{ext}"
           counter += 1
       return new_name
   ```

3. **Windows 权限处理局限性**：
   `rmdir_recursive` 中仅设置 `0o600` 权限，可能不足以应对某些系统限制（如只读属性）。建议增加 `os.chmod(..., stat.S_IWRITE)` 更健壮。

4. **`findAllDrives` 被注释**：
   当前无法枚举磁盘驱动器。如需恢复，请引入 `pywin32` 并取消注释相关代码。

---

## 许可证

默认遵循 Python 软件基金会许可证（PSF License），允许自由使用、修改和分发。

---

## 更新建议（TODO）

| 编号 | 建议内容 |
|------|----------|
| 1 | 修复 `timestamp2datatiemStr` 拼写错误 |
| 2 | 补全 `getFileName()` 函数实现 |
| 3 | 添加单元测试样例 |
| 4 | 增加日志记录功能（可选） |
| 5 | 文档化异常处理机制 |
| 6 | 提供 `movefile`, `movedir` 扩展功能 |

---

> ✅ 本模块适合作为基础组件集成至各类文件管理系统、备份工具、资源上传服务中。