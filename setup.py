#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
카드 리더기 프로그램 설치 스크립트
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="card-reader",
    version="1.0.0",
    author="Card Reader Team",
    description="ISO/IEC 14443 Type A/B 카드 리더기 프로그램",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/card_reader",
    py_modules=["card_reader", "card_reader_web"],
    install_requires=[
        "pyscard>=2.0.0",
        "pyperclip>=1.8.2",
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "jinja2>=3.1.2",
    ],
    entry_points={
        "console_scripts": [
            "card-reader=card_reader_web:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
)

