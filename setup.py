#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
The setup file for installing the library
"""
import os
from setuptools import find_packages
from setuptools import setup

version = '1.0.1'

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()
except IOError:
    README = CHANGES = ''



install_requires = [
    'numpy',
    ]

tests_require = [
    'mock',
    'pytest',
    'pytest-cov',
    'pytest-pep8',
    ]

setup(
    name="python-twitch-stream",
    version=version,
    description="An interface to the Twitch website, to interact with "
                "their video and chat",
    long_description="\n\n".join([README, CHANGES]),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Other Audience",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Topic :: Communications :: Chat :: Internet Relay Chat",
        "Topic :: Multimedia :: Video"
        ],
    keywords="twitch, stream, video, chat",
    author="Jonas Degrave",
    author_email="erstaateenknolraapinmijntuin+pythontwitch@gmail.com",
    url="https://github.com/317070/python-twitch-stream",
    license="MIT",
    packages=find_packages(),
    include_package_data=False,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'testing': tests_require,
        },
    )