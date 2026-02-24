import qrcode

def gen_qr(data, path):
	qr = =qrcode.QRCode(
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

