#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="toolbar-events-plugin",
    version="1.0.0",
    author="Codegen",
    author_email="info@codegen.com",
    description="Events plugin for the Toolbar application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Zeeeepa/toolbar",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    include_package_data=True,
    package_data={
        "": ["*.json", "*.svg", "*.md"],
    },
    entry_points={
        "toolbar.plugins": [
            "events=Toolbar.plugins.events:EventsPlugin",
        ],
    },
)
