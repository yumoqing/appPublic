from PIL import Image
import qrcode

def gen_qr(data, path):
	qr = qrcode.QRCode(
		version=1,            # 控制二维码大小（1~40）
		error_correction=qrcode.constants.ERROR_CORRECT_L,  # 容错率 L(7%)、M(15%)、Q(25%)、H(30%)
		box_size=10,          # 每个格子的像素大小
		border=4,             # 边框宽度（最小为4）
	)
	qr.add_data(data)
	qr.make(fit=True)  # 自动调整版本以适应数据

	# 生成图像
	img = qr.make_image(fill_color="black", back_color="white")
	img.save(path)


def gen_qr_withlogo(data, path, logopath=None, logoloc='cc'):
	"""
	data: 二维码数据
	path：二维码保存路径
	logopath: logo图标路径
	logoloc: logo存放路径， cc：中心，br：右下
	"""

	# 1. 创建高纠错二维码（即使放角落也建议保留 H 级）
	qr = qrcode.QRCode(
		version=5,
		error_correction=qrcode.constants.ERROR_CORRECT_H,  # 仍建议保留
		box_size=10,
		border=4,
	)
	data = "https://www.example.com"
	qr.add_data(data)
	qr.make(fit=True)

	qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
	qr_width, qr_height = qr_img.size

	if logopath:
		# 2. 加载并调整 Logo 大小
		logo = Image.open(logopath)  # 支持 PNG（含透明通道）
		# 比居中时可稍大一点，但仍建议 ≤1/5
		logo_size = min(qr_width, qr_height) // 5  
		logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
		if logoloc == 'br':
			# 3. 计算右下角位置（留3一点边距更美观）
			margin = 10  # 距离右边缘和下边缘的像素
			pos = (qr_width - logo_size - margin, qr_height - logo_size - margin)
		else:
			pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
		# 4. 粘贴 Logo（自动处理透明通道）
		qr_img.paste(logo, pos, mask=logo.split()[-1] if logo.mode in ('RGBA', 'LA') else None)

	# 5. 保存
	qr_img.save(path)
