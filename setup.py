# -*- coding: utf-8 -*-


from distutils.core import setup
from setuptools import setup, find_packages

# usage:
# python setup.py bdist_wininst generate a window executable file
# python setup.py bdist_egg generate a egg file
# Release information about eway

version = "5.1.1"
name = "appPublic"
description = "appPublic"
author = "yumoqing"
email = "yumoqing@gmail.com"

packages=find_packages()
package_data = {}

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="appPublic",
    version=version,
    
    # uncomment the following lines if you fill them out in release.py
    description=description,
    author=author,
    author_email=email,
   
    install_requires=[
    ],
    packages=packages,
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
