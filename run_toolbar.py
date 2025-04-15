#!/usr/bin/env python3
"""
Convenience script to run the Toolbar application without installing it.
"""

import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import and run the main function
from Toolbar.main import main

if __name__ == "__main__":
    sys.exit(main())
