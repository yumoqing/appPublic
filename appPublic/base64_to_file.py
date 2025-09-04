import os
import re
import base64
from appPuyblic.uniqueID import getID

MIME_EXT = {
    # 图片
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/bmp": "bmp",
    "image/svg+xml": "svg",
    "image/x-icon": "ico",
    "image/tiff": "tiff",

    # 音频
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/ogg": "ogg",
    "audio/webm": "weba",
    "audio/aac": "aac",
    "audio/flac": "flac",
    "audio/mp4": "m4a",
    "audio/3gpp": "3gp",

    # 视频
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/ogg": "ogv",
    "video/x-msvideo": "avi",
    "video/quicktime": "mov",
    "video/x-matroska": "mkv",
    "video/3gpp": "3gp",
    "video/x-flv": "flv",
}

def getFilenameFromBase64(base64String):
	match = re.match(r"data:(.*?);base64,(.*)", base64String)
	if not match:
        raise ValueError("不是合法的 base64 Data URL")
	mime_type, b64_data = match.groups()
	ext = MIME_EXT.get(mime_type, mime_type.split("/")[-1])
	name = getID()
	fname = f'{name}.{ext}'
	return fname
}

def base64_to_file(base64_string, output_path):
	# Remove data URL prefix if present (e.g., "data:image/png;base64,")
	if ',' in base64_string:
		header, base64_data = base64_string.split(',', 1)
	else:
		base64_data = base64_string

	# Decode Base64 string
	binary_data = base64.b64decode(base64_data)
	
	# Write binary data to file
	with open(output_path, 'wb') as file:
		file.write(binary_data)
