"""
honeydb setup
"""

import os
from setuptools import setup

HERE = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(HERE, "README.rst")) as f:
    LONG_DESC = f.read()

setup(
    name="honeydb",
    version="1.4.0",
    author="foospidy",
    description=("A Python API wrapper and CLI tool for the HoneyDB."),
    license="MIT",
    keywords="wrapper library honeydb api cli",
    url="https://honeydb.io",
    download_url="https://github.com/honeydbio/honeydb-python",
    packages=["honeydb", "honeydb.api"],
    long_description=LONG_DESC,
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=["requests"],
    scripts=["honeydb/bin/honeydb"],
)
