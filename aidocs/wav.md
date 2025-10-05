# 音频格式转换工具文档

## 概述

该模块提供了一个简单的音频处理函数，用于将任意 `.wav` 音频文件转换为 **16kHz 采样率、单声道（Mono）** 的标准格式。此格式常用于语音识别、语音合成等语音处理任务中，以确保输入音频满足模型要求。

使用了 `pydub` 库进行音频操作，依赖于 `ffmpeg` 或 `libav` 作为后端处理引擎。

---

## 依赖库

- `pydub`
- `ffmpeg`（需系统安装）

### 安装方法

```bash
pip install pydub
```

请确保系统中已安装 `ffmpeg`：
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
- **Windows**: 下载并添加 `ffmpeg` 到系统环境变量，或通过 [https://ffmpeg.org](https://ffmpeg.org) 安装

---

## 函数说明

### `convert_to_16k_mono(in_wav_path: str, out_wav_path: str) -> None`

将指定路径的 WAV 音频文件转换为 16kHz 采样率、单声道格式，并保存到输出路径。

#### 参数

| 参数名         | 类型   | 说明                         |
|----------------|--------|------------------------------|
| `in_wav_path`  | `str`  | 输入音频文件路径（必须是 WAV 格式） |
| `out_wav_path` | `str`  | 输出音频文件保存路径             |

#### 功能

1. 使用 `AudioSegment.from_wav()` 加载输入音频。
2. 将音频采样率设置为 16000 Hz。
3. 将声道数设置为 1（单声道）。
4. 导出处理后的音频为 WAV 格式至指定路径。

#### 示例用法

```python
convert_to_16k_mono("input.wav", "output_16k_mono.wav")
```

#### 注意事项

- 输入文件必须是有效的 `.wav` 文件。
- 输出目录需存在，否则会抛出异常。
- 若输出文件已存在，将被覆盖。

---

## 典型应用场景

- 为 ASR（自动语音识别）系统准备标准化输入音频。
- 统一不同来源音频的格式以便批量处理。
- 减少音频数据大小（降低采样率和声道数）。

---

## 完整示例代码

```python
from pydub import AudioSegment

def convert_to_16k_mono(in_wav_path, out_wav_path):
    """
    将WAV音频转换为16kHz、单声道格式
    
    参数:
        in_wav_path (str): 输入音频路径
        out_wav_path (str): 输出音频路径
    """
    audio = AudioSegment.from_wav(in_wav_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(out_wav_path, format="wav")

# 使用示例
# convert_to_16k_mono("input.wav", "output_16k_mono.wav")
```

---

## 错误处理建议（扩展功能）

虽然当前版本未包含异常处理，但在生产环境中建议添加如下改进：

```python
import os
from pydub import AudioSegment

def convert_to_16k_mono(in_wav_path, out_wav_path):
    if not os.path.exists(in_wav_path):
        raise FileNotFoundError(f"输入文件不存在: {in_wav_path}")
    
    try:
        audio = AudioSegment.from_wav(in_wav_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(out_wav_path, format="wav")
    except Exception as e:
        raise RuntimeError(f"音频转换失败: {e}")
```

---

## 许可与版权

本代码为开源示例，遵循 MIT 风格许可，可用于学习、研究及商业项目（请根据实际依赖库的许可证合规使用）。