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

from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen, QVBoxLayout, QLabel, QPushButton, QDialog

# Import custom modules
# Use try-except for core imports to make the application more robust
try:
    from Toolbar.core.config import Config, get_config_instance
    from Toolbar.core.plugin_system import PluginManager
except ImportError as e:
    # Log the error
    print(f"Critical import error: {e}")
    
    # Define fallback classes if imports fail
    class Config:
        def __init__(self):
            self.settings = {}
        
        def get_setting(self, key, default=None):
            return self.settings.get(key, default)
        
        def set_setting(self, key, value):
            self.settings[key] = value
    
    def get_config_instance():
        return Config()
    
    class PluginManager:
        def __init__(self, config):
            self.config = config
            self.plugins = {}
            self.plugin_dirs = []
            self.failed_plugins = {}
        
        def add_plugin_directory(self, directory):
            if os.path.isdir(directory) and directory not in self.plugin_dirs:
                self.plugin_dirs.append(directory)
        
        def load_plugins(self):
            pass
        
        def cleanup(self):
            pass

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

class PluginErrorDialog(QDialog):
    """Dialog to display plugin loading errors."""
    
    def __init__(self, failed_plugins, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plugin Loading Errors")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout()
        
        # Add error message
        error_label = QLabel("Some plugins failed to load. The application will continue with limited functionality.")
        error_label.setWordWrap(True)
        layout.addWidget(error_label)
        
        # Add failed plugins list
        for plugin_name, error_msg in failed_plugins.items():
            plugin_label = QLabel(f"<b>{plugin_name}</b>: {error_msg}")
            plugin_label.setWordWrap(True)
            layout.addWidget(plugin_label)
        
        # Add continue button
        continue_button = QPushButton("Continue Anyway")
        continue_button.clicked.connect(self.accept)
        layout.addWidget(continue_button)
        
        self.setLayout(layout)

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
        
        # Load plugins with error handling
        try:
            plugin_manager.load_plugins()
            logger.info("Plugins loaded")
            
            # Check for failed plugins
            failed_plugins = plugin_manager.get_failed_plugins()
            if failed_plugins:
                logger.warning(f"Some plugins failed to load: {failed_plugins}")
                
                # Show error dialog
                error_dialog = PluginErrorDialog(failed_plugins)
                error_dialog.exec_()
        except Exception as e:
            logger.error(f"Error loading plugins: {e}", exc_info=True)
            # Continue execution even if plugins fail to load
            QMessageBox.warning(
                None,
                "Plugin Loading Error",
                f"Error loading plugins: {str(e)}\n\nThe application will continue with limited functionality."
            )
        
        # Import ScriptToolbar here to avoid circular imports
        try:
            from Toolbar.plugins.automationmanager.ui.script_toolbar_ui import ScriptToolbar
            # Create and show the toolbar
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
