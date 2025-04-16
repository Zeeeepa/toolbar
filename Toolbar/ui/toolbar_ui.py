"""
Toolbar UI implementation.
"""
import logging
import os
from typing import Dict, Optional

from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QIcon, QScreen
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QPushButton,
    QSystemTrayIcon, QMenu, QAction, QDesktopWidget,
    QDialog, QApplication
)

from ..core.config import Config
from ..core.enhanced_plugin_system import EnhancedPlugin
from .notification_widget import NotificationWidget
from .plugin_button import PluginButton
from .toolbar_settings import SettingsDialog
from .plugin_manager import PluginManagerDialog

logger = logging.getLogger(__name__)

class ToolbarUI(QMainWindow):
    """Main toolbar window."""

    def __init__(self, app):
        """Initialize the toolbar UI."""
        super().__init__()
        self.app = app
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components."""
        # Set window flags for taskbar-like behavior
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QHBoxLayout(central_widget)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        
        # Set window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2D2D2D;
                border-top: 1px solid #3D3D3D;
            }
        """)
        
        # Initialize UI components
        self._init_tray()
        self._load_plugins()
        
        # Position window at bottom of screen
        self._position_window()
        
        logger.info("UI components initialized")
        
    def _init_tray(self):
        """Initialize system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_menu = QMenu()
        
        # Add menu actions
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        self.tray_menu.addAction(show_action)
        
        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)
        self.tray_menu.addAction(hide_action)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.app.quit)
        self.tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
        
        logger.info("System tray icon created")
        
    def _load_plugins(self):
        """Load and add plugin buttons"""
        loaded_count = 0
        for plugin in self.app.plugin_manager.get_plugins():
            try:
                button = PluginButton(plugin, self)
                self.layout.addWidget(button)
                loaded_count += 1
                logger.info(f"Added button for plugin: {plugin.name}")
            except Exception as e:
                logger.error(f"Error creating button for plugin {plugin.name}: {str(e)}")
                logger.exception(e)
        
        # Add stretch to keep buttons left-aligned
        self.layout.addStretch()
        logger.info(f"Loaded {loaded_count} plugin buttons")
        
    def _position_window(self):
        """Position window at bottom of screen with proper dimensions"""
        screen = QScreen.virtualGeometry(QApplication.primaryScreen())
        
        # Set window height
        window_height = 50
        
        # Calculate position
        x = screen.x()
        y = screen.height() - window_height
        width = screen.width()
        
        # Set geometry
        self.setGeometry(x, y, width, window_height)
        logger.info(f"Positioned toolbar at ({x}, {y})")
        
    def show(self):
        """Show the toolbar"""
        super().show()
        self.raise_()
        self.activateWindow()
        
    def hide(self):
        """Hide the toolbar"""
        super().hide()

    def show_settings(self):
        """Show the settings dialog."""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self.config, self)
            
        self.settings_dialog.show()
        logger.info("Settings dialog shown")

    def show_plugin_manager(self):
        """Show the plugin manager dialog."""
        if not self.plugin_manager_dialog:
            self.plugin_manager_dialog = PluginManagerDialog(self.plugins, self)
            
        # Reload plugins when dialog is closed
        if self.plugin_manager_dialog.exec_() == QDialog.Accepted:
            self._reload_plugins()
            
        logger.info("Plugin manager dialog shown")

    def _reload_plugins(self):
        """Reload all plugin buttons."""
        # Remove existing buttons
        for i in reversed(range(self.centralWidget().layout().count())):
            self.centralWidget().layout().itemAt(i).widget().setParent(None)
            
        # Reload buttons
        self._load_plugins(self.centralWidget().layout())

    def show_notification(self, title: str, message: str, duration: Optional[int] = None):
        """Show a notification."""
        self.notification_widget.show_notification(title, message, duration)
