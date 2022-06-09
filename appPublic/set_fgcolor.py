# -*- coding=utf-8 -*-

"""
kivy color:
[ r, g, b, a]
不同的颜色值总能找到一个人眼感知的灰度值，这是著名的心理学公式：
灰度 = 红×0.299 + 绿×0.587 + 蓝×0.114
当灰度值大于0.5时使用暗色，否则使用明色
"""

def get_fgcolor_from_bgcolor(bgcolor):
	dark_fgcolor=[0.11,0.11,0.11,1]
	bright_fgcolor=[0.89,0.89,0.89,1]
	graylevel = 0.299 * bgcolor[0] + \
				0.587 * bgcolor[1] + \
				0.114 * bgcolor[2]
	if graylevel > 0.5:
		return dark_fgcolor
	else:
		return bright_fgcolor
