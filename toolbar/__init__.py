"""
Toolbar - A modular taskbar application with plugin support.

This package provides a customizable toolbar application with plugin support
for GitHub, Linear, template prompts, auto-scripting, and event automation.
"""

# Version information
__version__ = "0.1.0"

# Import main entry point
from .main import main

# Make main function available at package level
__all__ = ['main']
