#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="toolkit",
    version="1.0.0",
    description="A modular taskbar application with plugin support",
    author="Zeeeepa",
    author_email="info@zeeeepa.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyQt5>=5.15.0",
        "requests>=2.25.0",
        "pynput>=1.7.0",
        "pyautogui>=0.9.50",
        "keyboard>=0.13.0",
        "pyperclip>=1.8.0",
        "python-dotenv>=0.15.0",
        "appdirs>=1.4.4",
    ],
    entry_points={
        "console_scripts": [
            "toolbar=toolkit.toolbar.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
)
