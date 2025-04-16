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
from typing import Optional, List, Dict, Any
import importlib.util
import signal
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load environment variables from .env file if it exists
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
if os.path.exists(dotenv_path):
    dotenv.load_dotenv(dotenv_path)

from PyQt5.QtWidgets import (
    QApplication, QMessageBox, QSplashScreen, QVBoxLayout, QLabel, 
    QPushButton, QDialog, QMainWindow, QWidget, QHBoxLayout, QTabWidget,
    QTextEdit, QCheckBox, QGroupBox, QScrollArea
)
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtCore import Qt

# Import custom modules
# Use try-except for core imports to make the application more robust
try:
    from Toolbar.core.config import Config, get_config_instance
    from Toolbar.core.plugin_system import PluginManager, Plugin, PluginType, PluginState
    from Toolbar.core.enhanced_plugin_system import EnhancedPluginManager
    from Toolbar.ui.toolbar_ui import ToolbarUI  # Import the ToolbarUI class from ui module
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
        
        def save(self):
            pass
    
    def get_config_instance():
        return Config()
    
    class Plugin:
        def initialize(self, config):
            pass
        
        def cleanup(self):
            pass
        
        @property
        def name(self):
            return "Fallback Plugin"
        
        @property
        def version(self):
            return "0.0.0"
        
        @property
        def description(self):
            return "Fallback plugin when real plugins can't be loaded"
    
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
        
        def get_all_plugins(self):
            return {}
        
        def get_failed_plugins(self):
            return {}
        
        def cleanup(self):
            pass
    
    # Define fallback enums
    class PluginType:
        CORE = "core"
        UI = "ui"
        INTEGRATION = "integration"
        AUTOMATION = "automation"
        UTILITY = "utility"
        OTHER = "other"
    
    class PluginState:
        UNLOADED = "unloaded"
        LOADED = "loaded"
        ACTIVATED = "activated"
        DEACTIVATED = "deactivated"
        ERROR = "error"
    
    # Define fallback ToolbarUI class if the import fails
    class ToolbarUI(QMainWindow):
        def __init__(self, config, plugin_manager):
            super().__init__()
            self.setWindowTitle("Fallback Toolbar")
            self.config = config
            self.plugin_manager = plugin_manager
    
    class EnhancedPluginManager(PluginManager):
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

class FallbackToolbar(QMainWindow):
    """Fallback toolbar UI when the main UI can't be loaded."""
    
    def __init__(self, config, plugin_manager, error_message=None):
        super().__init__()
        self.config = config
        self.plugin_manager = plugin_manager
        self.error_message = error_message or "Failed to load the main toolbar UI"
        
        self.setWindowTitle("Toolbar (Fallback Mode)")
        self.setMinimumSize(600, 400)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        main_layout = QVBoxLayout(central_widget)
        
        # Add error message
        error_label = QLabel(f"<b>Error:</b> {self.error_message}")
        error_label.setWordWrap(True)
        error_label.setStyleSheet("color: red; font-size: 14px;")
        main_layout.addWidget(error_label)
        
        # Add tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Add error details tab
        error_tab = QWidget()
        error_layout = QVBoxLayout(error_tab)
        
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setPlainText(traceback.format_exc())
        error_layout.addWidget(self.error_text)
        
        self.tab_widget.addTab(error_tab, "Error Details")
        
        # Add plugins tab
        plugins_tab = QWidget()
        plugins_layout = QVBoxLayout(plugins_tab)
        
        # Add loaded plugins section
        loaded_group = QGroupBox("Loaded Plugins")
        loaded_layout = QVBoxLayout(loaded_group)
        
        loaded_plugins = plugin_manager.get_all_plugins()
        if loaded_plugins:
            for name, plugin in loaded_plugins.items():
                plugin_label = QLabel(f"<b>{name}</b> v{plugin.version}")
                loaded_layout.addWidget(plugin_label)
                
                desc_label = QLabel(plugin.description)
                desc_label.setWordWrap(True)
                desc_label.setIndent(20)
                loaded_layout.addWidget(desc_label)
        else:
            loaded_layout.addWidget(QLabel("No plugins loaded"))
        
        loaded_layout.addStretch()
        plugins_layout.addWidget(loaded_group)
        
        # Add failed plugins section
        failed_group = QGroupBox("Failed Plugins")
        failed_layout = QVBoxLayout(failed_group)
        
        failed_plugins = plugin_manager.get_failed_plugins()
        if failed_plugins:
            for name, error in failed_plugins.items():
                plugin_label = QLabel(f"<b>{name}</b>: {error}")
                plugin_label.setWordWrap(True)
                plugin_label.setStyleSheet("color: red;")
                failed_layout.addWidget(plugin_label)
        else:
            failed_layout.addWidget(QLabel("No failed plugins"))
        
        failed_layout.addStretch()
        plugins_layout.addWidget(failed_group)
        
        self.tab_widget.addTab(plugins_tab, "Plugins")
        
        # Add settings tab
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        
        # Add a note about settings
        settings_layout.addWidget(QLabel("Basic settings are available in fallback mode:"))
        
        # Add some basic settings
        self.auto_start_checkbox = QCheckBox("Start on system boot")
        self.auto_start_checkbox.setChecked(config.get_setting("auto_start", False))
        self.auto_start_checkbox.toggled.connect(lambda checked: config.set_setting("auto_start", checked))
        settings_layout.addWidget(self.auto_start_checkbox)
        
        self.minimize_to_tray_checkbox = QCheckBox("Minimize to system tray")
        self.minimize_to_tray_checkbox.setChecked(config.get_setting("minimize_to_tray", True))
        self.minimize_to_tray_checkbox.toggled.connect(lambda checked: config.set_setting("minimize_to_tray", checked))
        settings_layout.addWidget(self.minimize_to_tray_checkbox)
        
        settings_layout.addStretch()
        self.tab_widget.addTab(settings_tab, "Settings")
        
        # Add buttons
        buttons_layout = QHBoxLayout()
        main_layout.addLayout(buttons_layout)
        
        reload_button = QPushButton("Reload Toolbar")
        reload_button.clicked.connect(self.reload_toolbar)
        buttons_layout.addWidget(reload_button)
        
        disable_plugins_button = QPushButton("Disable Problematic Plugins")
        disable_plugins_button.clicked.connect(self.disable_problematic_plugins)
        buttons_layout.addWidget(disable_plugins_button)
        
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)
        buttons_layout.addWidget(exit_button)
    
    def reload_toolbar(self):
        """Attempt to reload the toolbar."""
        QMessageBox.information(
            self,
            "Reload Toolbar",
            "The application will now restart. Please relaunch the toolbar."
        )
        self.close()
        # Restart the application
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    def disable_problematic_plugins(self):
        """Disable all plugins that failed to load."""
        failed_plugins = self.plugin_manager.get_failed_plugins()
        
        if not failed_plugins:
            QMessageBox.information(
                self,
                "No Failed Plugins",
                "There are no failed plugins to disable."
            )
            return
        
        # Create a dialog to select plugins to disable
        dialog = QDialog(self)
        dialog.setWindowTitle("Disable Problematic Plugins")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Select plugins to disable:"))
        
        # Create checkboxes for each failed plugin
        checkboxes = {}
        for name in failed_plugins.keys():
            checkbox = QCheckBox(name)
            checkbox.setChecked(True)
            checkboxes[name] = checkbox
            layout.addWidget(checkbox)
        
        # Add buttons
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)
        
        disable_button = QPushButton("Disable Selected")
        disable_button.clicked.connect(lambda: self._disable_selected_plugins(checkboxes, dialog))
        buttons_layout.addWidget(disable_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_button)
        
        dialog.exec_()
    
    def _disable_selected_plugins(self, checkboxes, dialog):
        """Disable the selected plugins."""
        disabled_count = 0
        
        for name, checkbox in checkboxes.items():
            if checkbox.isChecked():
                try:
                    # Try to disable the plugin
                    if hasattr(self.plugin_manager, "disable_plugin"):
                        self.plugin_manager.disable_plugin(name)
                        disabled_count += 1
                except Exception as e:
                    logger.error(f"Error disabling plugin {name}: {e}", exc_info=True)
        
        if disabled_count > 0:
            QMessageBox.information(
                self,
                "Plugins Disabled",
                f"{disabled_count} plugin(s) have been disabled. Please restart the application."
            )
            dialog.accept()
        else:
            QMessageBox.warning(
                self,
                "No Plugins Disabled",
                "No plugins were disabled. Please select at least one plugin."
            )

class PluginErrorDialog(QDialog):
    """Dialog to display plugin loading errors."""
    
    def __init__(self, failed_plugins, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plugin Loading Errors")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout(self)
        
        # Add error message
        error_label = QLabel("Some plugins failed to load. The application will continue with limited functionality.")
        error_label.setWordWrap(True)
        layout.addWidget(error_label)
        
        # Create a scroll area for the failed plugins list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # Create a widget to hold the failed plugins list
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Add failed plugins list
        for plugin_name, error_msg in failed_plugins.items():
            plugin_label = QLabel(f"<b>{plugin_name}</b>: {error_msg}")
            plugin_label.setWordWrap(True)
            scroll_layout.addWidget(plugin_label)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        
        # Add buttons
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)
        
        # Add disable button
        disable_button = QPushButton("Disable Failed Plugins")
        disable_button.clicked.connect(lambda: self._disable_failed_plugins(failed_plugins))
        buttons_layout.addWidget(disable_button)
        
        # Add continue button
        continue_button = QPushButton("Continue Anyway")
        continue_button.clicked.connect(self.accept)
        buttons_layout.addWidget(continue_button)
    
    def _disable_failed_plugins(self, failed_plugins):
        """Disable all failed plugins."""
        if not hasattr(plugin_manager, "disable_plugin"):
            QMessageBox.warning(
                self,
                "Not Supported",
                "Disabling plugins is not supported in this version."
            )
            return
        
        disabled_count = 0
        for plugin_name in failed_plugins.keys():
            try:
                plugin_manager.disable_plugin(plugin_name)
                disabled_count += 1
            except Exception as e:
                logger.error(f"Error disabling plugin {plugin_name}: {e}", exc_info=True)
        
        if disabled_count > 0:
            QMessageBox.information(
                self,
                "Plugins Disabled",
                f"{disabled_count} plugin(s) have been disabled. They will not be loaded on next startup."
            )
        
        self.accept()

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

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("toolbar.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

def show_error_dialog(title, message):
    """Show a message box with an error message."""
    QMessageBox.critical(None, title, message)

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

def close_gracefully():
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    if app:
        app.quit()
    sys.exit(0)

def main():
    """
    Main entry point for the Toolbar application.
    Initializes the application, loads configuration, and starts the UI.
    """
    try:
        # Initialize global variable at the beginning of the function
        global toolbar_instance, plugin_manager
        toolbar_instance = None
        
        # Configure logging
        setup_logging()
        logger.info("Starting Toolbar application")
        
        # Create QApplication instance
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        
        # Load configuration
        try:
            config = get_config_instance()
            logger.info("Configuration loaded")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}", exc_info=True)
            show_error_dialog("Configuration Error", f"Failed to load configuration: {str(e)}")
            return 1
        
        # Initialize plugin manager - use enhanced version if available
        try:
            # Check if we should use the enhanced plugin manager
            use_enhanced = config.get_setting("plugins.use_enhanced", True)
            
            if use_enhanced:
                try:
                    plugin_manager = EnhancedPluginManager(config)
                    logger.info("Using enhanced plugin manager")
                except Exception as e:
                    logger.error(f"Failed to initialize enhanced plugin manager: {e}", exc_info=True)
                    logger.info("Falling back to standard plugin manager")
                    plugin_manager = PluginManager(config)
            else:
                plugin_manager = PluginManager(config)
            
            plugin_manager.load_plugins()
            logger.info("Plugins loaded")
        except Exception as e:
            logger.error(f"Failed to initialize plugin manager: {e}", exc_info=True)
            show_error_dialog("Plugin Error", f"Failed to initialize plugin manager: {str(e)}")
            return 1
        
        # Initialize and show the toolbar UI
        try:
            # Create the toolbar
            toolbar = ToolbarUI(config, plugin_manager)
            
            # Set the toolbar instance in the plugin manager
            plugin_manager.set_toolbar(toolbar)
            
            # Show the toolbar
            toolbar.show()
            
            # Force the toolbar to show after a short delay
            QTimer.singleShot(500, lambda: force_show_toolbar(toolbar))
            
            logger.info("Toolbar UI initialized and displayed")
            
            # Store the toolbar instance globally
            toolbar_instance = toolbar
        except Exception as e:
            logger.error(f"Failed to initialize toolbar UI: {e}", exc_info=True)
            
            # Create a fallback UI
            fallback = FallbackToolbar(config, plugin_manager, f"Failed to initialize toolbar UI: {str(e)}")
            fallback.show()
            
            # Store the fallback instance globally
            toolbar_instance = fallback
        
        # Start the application event loop
        return app.exec_()
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}", exc_info=True)
        show_error_dialog("Critical Error", f"An unhandled exception occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
