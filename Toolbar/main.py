#!/usr/bin/env python3
import sys
import os
import warnings
import logging
import traceback
import dotenv
from PyQt5.QtCore import QTimer
import time
import threading
from typing import Optional
import importlib.util
import signal
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file if it exists
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    dotenv.load_dotenv(dotenv_path)

from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen

# Import custom modules
from Toolbar.core.config import Config, get_config_instance
from Toolbar.core.plugin_system import PluginManager
from Toolbar.ui.script_toolbar_ui import ScriptToolbar

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("toolbar.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suppress PyQt5 deprecation warnings
warnings.filterwarnings("ignore", message=".*sipPyTypeDict.*")

# Global variables
toolbar_instance = None
plugin_manager = None

def exception_hook(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions by logging them and showing a message box."""
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Show error message to user
    QMessageBox.critical(
        None,
        "Application Error",
        f"An unexpected error occurred:\n\n{str(exc_value)}\n\nPlease check the log file for details."
    )

def main():
    """Main application entry point."""
    # Set up global exception handler
    sys.excepthook = exception_hook
    
    logger.info("Starting Toolbar application")
    
    app = QApplication(sys.argv)
    
    try:
        # Initialize configuration
        config = get_config_instance()
        logger.info("Configuration loaded")
        
        # Initialize plugin manager
        global plugin_manager
        plugin_manager = PluginManager(config)
        
        # Add plugin directories
        plugin_manager.add_plugin_directory(os.path.join(os.path.dirname(__file__), "plugins"))
        
        # Load plugins
        plugin_manager.load_plugins()
        logger.info("Plugins loaded")
        
        # Create and show the toolbar
        try:
            toolbar = ScriptToolbar(config, plugin_manager)
            
            # First show attempt
            logger.info("Showing toolbar window")
            toolbar.show()
            
            # Force visibility with raise and activate
            toolbar.raise_()
            toolbar.activateWindow()
            
            # Wait a bit and show again to ensure visibility
            QTimer.singleShot(500, lambda: force_show_toolbar(toolbar))
            
            logger.info("Toolbar UI initialized and displayed")
        except Exception as e:
            logger.error(f"Failed to initialize toolbar UI: {e}", exc_info=True)
            QMessageBox.critical(
                None,
                "UI Error",
                f"Failed to initialize toolbar UI: {str(e)}\n\nCheck the log file for more details."
            )
            return 1
        
        # Start the application event loop
        return app.exec_()
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "Initialization Error",
            f"Failed to initialize application: {str(e)}"
        )
        return 1
    finally:
        # Clean up plugins
        if plugin_manager:
            plugin_manager.cleanup()

def force_show_toolbar(toolbar):
    """Force the toolbar to be visible by showing and raising it again."""
    try:
        logger.info(f"Force showing toolbar. Current geometry: {toolbar.geometry().x()}, {toolbar.geometry().y()}, {toolbar.width()}x{toolbar.height()}")
        logger.info(f"Current window flags: {toolbar.windowFlags()}")
        logger.info(f"Current opacity: {toolbar.windowOpacity()}")
        
        # Show and raise again
        toolbar.show()
        toolbar.raise_()
        toolbar.activateWindow()
        
        # Log the final position
        logger.info(f"Toolbar position after force show: {toolbar.geometry().x()}, {toolbar.geometry().y()}, {toolbar.width()}x{toolbar.height()}")
    except Exception as e:
        logger.error(f"Error in force_show_toolbar: {e}", exc_info=True)

if __name__ == "__main__":
    sys.exit(main())
