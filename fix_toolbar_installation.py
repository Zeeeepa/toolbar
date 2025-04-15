#!/usr/bin/env python3
"""
Fix script for Toolbar installation issues.
This script ensures the Toolbar package is properly installed and accessible.
"""

import os
import sys
import subprocess
import platform

def main():
    """
    Main function to fix Toolbar installation issues.
    """
    print("Toolbar Installation Fix Utility")
    print("================================")
    
    # Check if we're running from the project directory
    if not os.path.exists("Toolbar") or not os.path.isdir("Toolbar"):
        print("Error: This script must be run from the toolkit project directory.")
        print("Please navigate to the directory containing the 'Toolbar' folder.")
        return 1
    
    # Check Python version
    python_version = platform.python_version()
    print(f"Python version: {python_version}")
    
    # Check if Toolbar is installed
    try:
        import Toolbar
        print(f"Toolbar package is installed at: {Toolbar.__file__}")
    except ImportError:
        print("Toolbar package is not installed or not in the Python path.")
        
        # Install the package in development mode
        print("\nInstalling Toolbar package in development mode...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
            print("Installation successful!")
        except subprocess.CalledProcessError as e:
            print(f"Error during installation: {e}")
            return 1
    
    # Verify installation
    print("\nVerifying installation...")
    try:
        import Toolbar
        from Toolbar.ui.toolbar_ui import Toolbar as ToolbarClass
        print("✓ Toolbar package is now properly installed.")
        print(f"  - Package location: {Toolbar.__file__}")
        print(f"  - Toolbar class location: {ToolbarClass.__module__}")
        print("\nYou should now be able to run the toolbar application.")
    except ImportError as e:
        print(f"Error: {e}")
        print("Installation verification failed.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
