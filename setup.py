# -*- coding: utf-8 -*-

from  appPublic.version import __version__
try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

with open('appPublic/version.py', 'r') as f:
	x = f.read()
	y = x[x.index("'")+1:]
	z = y[:y.index("'")]
	version = z
with open("README.md", "r") as fh:
    long_description = fh.read()

name = "appPublic"
description = "appPublic"
author = "yumoqing"
email = "yumoqing@gmail.com"

package_data = {}

setup(
	name="appPublic",
	version=version,
	
	# uncomment the following lines if you fill them out in release.py
	description=description,
	author=author,
	author_email=email,
   	platforms='any',
	install_requires=[
	],
	packages=[
		"appPublic"
	],
	package_data=package_data,
	keywords = [
	],
	url="https://github.com/yumoqing/appPublic",
	long_description=long_description,
	long_description_content_type="text/markdown",
	classifiers = [
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 3',
		'License :: OSI Approved :: MIT License',
	],
)
