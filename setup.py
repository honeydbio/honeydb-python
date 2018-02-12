"""
honeydb setup
"""
import os
from setuptools import setup

HERE = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(HERE, 'README.rst')) as f:
    LONG_DESC = f.read()

setup(
    name="honeydb",
    version="0.0.3",
    author="foospidy",
    description=("A python wrapper for the HoneyDB API - "
                 "https://riskdiscovery.com/honeydb/#threats"),
    license="MIT",
    keywords="wrapper library honeydb api",
    url="https://github.com/foospidy/honeydb-python",
    download_url="https://github.com/foospidy/honeydb-python",
    packages=['honeydb', 'honeydb.api'],
    long_description=LONG_DESC,
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=['requests', 'pyopenssl'],
    scripts=['honeydb/bin/honeydb'],
)
