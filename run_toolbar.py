#!/usr/bin/env python3
"""
Entry point script for running the Toolbar application.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from Toolbar.main import main

if __name__ == "__main__":
    sys.exit(main())
