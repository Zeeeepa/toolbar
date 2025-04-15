#!/usr/bin/env python3
"""
Setup script for the Toolbar application.
"""

from setuptools import setup, find_packages

setup(
    name="Toolbar",
    version="1.0.0",
    description="A customizable toolbar for running scripts and integrating with GitHub and Linear",
    author="Zeeeepa",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15.0",
        "requests>=2.25.0",
        "pynput>=1.7.0",
        "pyautogui>=0.9.50",
        "keyboard>=0.13.0",
        "pyperclip>=1.8.0",
        "python-dotenv>=0.15.0",
    ],
    entry_points={
        "console_scripts": [
            "toolbar=Toolbar.main:main",
        ],
    },
    include_package_data=True,
    python_requires=">=3.6",
)
