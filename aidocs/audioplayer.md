# `AudioPlayer` 技术文档

基于 `ffpyplayer` 的 Python 音频播放器类，支持加载音频文件、播放控制（播放/暂停/停止）、循环播放、音量调节和事件回调等功能。

---

## 📦 概述

`AudioPlayer` 是一个轻量级的音频播放器封装类，利用 `ffpyplayer` 库实现对本地音频文件的播放控制。该类提供了简洁的接口用于常见操作，如播放、暂停、跳转、循环等，并支持自定义事件处理。

---

## 🧩 依赖库

- `ffpyplayer`: 多媒体播放后端（基于 FFmpeg）
- `time`: 用于时间相关操作

```bash
pip install ffpyplayer
```

> ⚠️ 注意：`ffpyplayer` 在某些平台上可能需要手动编译或安装预构建版本。

---

## 🧱 类定义

### `class AudioPlayer(source=None, autoplay=False, loop=False, on_stop=None)`

初始化一个音频播放器实例。

#### 参数说明：

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `source` | `str` 或 `None` | `None` | 音频文件路径（可选，在初始化时设置或后续通过 `set_source()` 设置） |
| `autoplay` | `bool` | `False` | 是否在加载音频后自动开始播放 |
| `loop` | `bool` | `False` | 是否启用循环播放模式 |
| `on_stop` | `callable` 或 `None` | `None` | 当音频停止时调用的回调函数 |

---

## 🔧 属性列表

| 属性名 | 类型 | 描述 |
|--------|------|------|
| `volume` | `float` | 当前音量（范围 0.0 ~ 1.0），默认为 `1.0` |
| `state` | `str` | 当前状态：`'play'`, `'pause'`, `'stop'` |
| `source` | `str` | 当前音频源路径 |
| `quitted` | `bool` | 标记是否已请求退出（内部使用） |
| `loop` | `bool` | 是否开启循环播放 |
| `autoplay` | `bool` | 是否自动播放 |
| `player` | `MediaPlayer` 实例或 `None` | `ffpyplayer.player.MediaPlayer` 对象 |
| `on_stop` | `callable` 或 `None` | 停止播放时触发的用户回调函数 |
| `cmds` | `list` | （预留）命令队列（当前未使用） |

---

## 📚 方法说明

### `set_source(source: str)`
设置音频源并立即加载。

**参数：**
- `source` (str): 音频文件路径

**行为：**
- 更新 `self.source`
- 调用 `load()` 加载新资源

---

### `load() -> None`
加载当前 `source` 指定的音频文件。

**逻辑流程：**
1. 若无 `source`，直接返回。
2. 卸载已有播放器（调用 `unload()`）。
3. 创建新的 `MediaPlayer` 实例，配置选项：
   - `vn=True`: 禁用视频流
   - `sn=True`: 启用字幕流（不影响音频）
4. 使用 `callback` 和 `loglevel='info'`
5. 等待最多 10 秒获取音频元数据（尤其是 duration）
6. 初始暂停播放器以准备控制
7. 设置音量
8. 若 `autoplay=True`，则调用 `play()`

> ⚠️ **注意**：此方法包含阻塞等待（最大 10s），用于确保能读取到音频时长信息。

---

### `unload() -> None`
释放当前播放器资源，重置状态。

**效果：**
- 清空 `player`
- 设置状态为 `'stop'`
- 重置 `quitted` 标志

---

### `__del__()`
析构函数，确保对象销毁时调用 `unload()`。

---

### `play() -> None`
开始播放音频。

**行为：**
- 若尚未加载，则先调用 `load()`
- 若已在播放状态，直接返回
- 否则调用 `toggle_pause()` 并更新状态为 `'play'`

---

### `pause() -> None`
暂停播放。

**行为：**
- 若未加载，尝试加载
- 若已在暂停状态，不执行操作
- 否则调用 `toggle_pause()` 并更新状态为 `'pause'`

---

### `stop() -> None`
停止播放，重置播放位置至开头。

**行为：**
- 如果正在播放，先暂停
- 将播放进度跳转至 0（`seek(0)`）
- 更新状态为 `'stop'`
- 触发 `on_stop` 回调（如果存在）

---

### `seek(pos: float) -> None`
跳转到指定时间点（单位：秒）。

**参数：**
- `pos` (float): 目标时间位置（绝对时间）

**示例：**
```python
p.seek(30.0)  # 跳转到第30秒
```

---

### `get_pos() -> float`
获取当前播放时间（单位：秒）。

**返回：**
- 当前播放时间戳（PTS），若无播放器则返回 `0`

---

### `is_busy() -> bool`
判断是否正在播放中。

**返回：**
- `True` 表示处于 `'play'` 状态且有有效播放器
- `False` 表示暂停或停止

---

### `player_callback(selector: str, value: any)`
内部回调函数，由 `ffpyplayer` 触发。

**触发事件：**
- `'quit'`: 播放器退出 → 调用 `close()` 清理资源
- `'eof'`: 播放结束 → 调用 `_do_eos()`

> ✅ 日志输出可用于调试。

---

### `_do_eos(*args) -> None`
处理播放结束（End of Stream）事件。

**行为：**
- 若启用 `loop`，则跳回开头继续播放
- 否则调用 `stop()` 结束播放

---

## 🎯 使用示例

### 基本使用

```python
from audio_player import AudioPlayer

def on_audio_stopped():
    print("音频已停止")

# 初始化播放器
player = AudioPlayer(
    source="music.mp3",
    autoplay=True,
    loop=True,
    on_stop=on_audio_stopped
)

# 控制播放
player.play()
time.sleep(5)
player.pause()
player.seek(10.0)  # 跳转到第10秒
player.play()

# 查询位置
print(f"当前时间: {player.get_pos()}s")

# 停止
player.stop()
```

### 手动交互式控制（主程序示例）

运行脚本时传入音频路径：

```bash
python audio_player.py /path/to/audio.mp3
```

交互命令：
- `play` — 开始播放
- `pause` — 暂停
- `stop` — 停止并归零
- `quit` — 退出程序

---

## ⚙️ 内部机制说明

### 播放器初始化选项 (`ff_opts`)
```python
ff_opts = {'vn': True, 'sn': True}
```
- `vn=True`: 忽略视频流（仅音频）
- `sn=True`: 启用字幕流（不影响播放）

### 元数据加载等待机制
使用 `time.perf_counter()` 最多等待 10 秒以获取 `duration`，避免因媒体分析过慢导致后续操作失败。

### 状态管理
通过 `self.state` 维护播放状态机，防止重复操作。

---

## ❗ 已知限制与注意事项

1. **线程安全**：未考虑多线程并发访问，建议在单线程环境中使用。
2. **异常处理**：缺少对无效文件路径、格式不支持等情况的捕获，需外部保障输入合法性。
3. **资源释放**：虽然有 `__del__`，但推荐显式调用 `unload()` 或及时删除引用。
4. **性能**：`load()` 中的循环等待可能导致短暂阻塞 UI（适用于非 GUI 场景）。
5. **日志级别**：固定为 `'info'`，可通过扩展参数暴露配置。

---

## 🛠️ 扩展建议

- 添加音量控制接口（如 `set_volume()`）
- 支持获取总时长 `get_duration()`
- 引入事件系统替代硬编码回调
- 支持网络流媒体 URL
- 增加错误处理与异常通知机制

---

## 📄 许可与版权

本代码基于 MIT 或类似自由许可发布（具体取决于 `ffpyplayer` 的使用条款）。请遵守其开源协议。

---

> 文档版本：v1.0  
> 最后更新：2025年4月5日