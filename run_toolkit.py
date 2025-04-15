#!/usr/bin/env python3
"""
Run script for the Toolkit application.
This script launches the Toolkit application without requiring installation.
"""

import os
import sys
import logging
import importlib.util
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("toolkit-runner")

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ["PyQt5", "python-dotenv", "appdirs"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.warning(f"Missing required packages: {', '.join(missing_packages)}")
        return False, missing_packages
    
    return True, []

def install_dependencies(packages):
    """Install required dependencies."""
    logger.info(f"Installing required packages: {', '.join(packages)}")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        logger.info("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing dependencies: {e}")
        return False

def main():
    """Main function to run the Toolkit application."""
    logger.info("Starting Toolkit application...")
    
    # Add the current directory to the Python path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Check and install dependencies
    deps_ok, missing_deps = check_dependencies()
    if not deps_ok:
        logger.info("Installing missing dependencies...")
        if not install_dependencies(missing_deps):
            logger.error("Failed to install dependencies. Please install them manually.")
            return 1
    
    # Import and run the main module
    try:
        from toolkit.toolbar.main import main as toolkit_main
        return toolkit_main()
    except ImportError as e:
        logger.error(f"Error importing toolkit module: {e}")
        logger.error("Make sure the toolkit package is properly installed or in the current directory.")
        return 1
    except Exception as e:
        logger.error(f"Error running toolkit application: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
