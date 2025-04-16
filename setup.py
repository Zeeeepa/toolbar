from setuptools import setup, find_packages

setup(
    name="toolbar",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6",
        "webm-muxer",
    ],
    entry_points={
        "console_scripts": [
            "start_toolbar=Toolbar.start_toolbar:main",
        ],
    },
)
