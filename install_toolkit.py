#!/usr/bin/env python3
"""
Installation script for the Toolkit application.
This script installs the Toolkit package in development mode.
"""

import os
import sys
import subprocess
import platform

def main():
    """
    Main function to install the Toolkit application.
    """
    print("Toolkit Installation Utility")
    print("===========================")
    
    # Check Python version
    python_version = platform.python_version()
    print(f"Python version: {python_version}")
    
    # Install the package in development mode
    print("\nInstalling Toolkit package in development mode...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
        print("Installation successful!")
    except subprocess.CalledProcessError as e:
        print(f"Error during installation: {e}")
        return 1
    
    # Verify installation
    print("\nVerifying installation...")
    try:
        import toolkit
        from toolkit.toolbar.main import main as toolbar_main
        print("✓ Toolkit package is now properly installed.")
        print(f"  - Package location: {toolkit.__file__}")
        print("\nYou should now be able to run the toolkit application using:")
        print("  - The 'toolbar' command")
        print("  - The 'run_toolkit.py' script")
    except ImportError as e:
        print(f"Error: {e}")
        print("Installation verification failed.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
