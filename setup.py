# -*- coding: utf-8 -*-


try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

# usage:
# python setup.py bdist_wininst generate a window executable file
# python setup.py bdist_egg generate a egg file
# Release information about eway

version = "5.1.4"
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
	long_description=description,
	long_description_content_type="text/markdown",
	classifiers = [
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 3',
		'License :: OSI Approved :: MIT License',
	],
)
