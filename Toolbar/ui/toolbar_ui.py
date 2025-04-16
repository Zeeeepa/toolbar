"""
Toolbar UI implementation.
"""
import logging
import os
from typing import Dict, Optional

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QPushButton,
    QSystemTrayIcon, QMenu, QAction, QDesktopWidget,
    QDialog
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

    def __init__(self, plugin_manager):
        """Initialize the toolbar UI."""
        super().__init__()
        self.plugin_manager = plugin_manager
        self.notification_widget = None
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
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Load plugin buttons
        self._load_plugins(layout)
        
        # Initialize notification widget
        self.notification_widget = NotificationWidget(self)
        logger.info("Notification widget initialized")
        
        # Set window properties
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
                border: none;
            }
        """)
        
        # Position toolbar at bottom of screen
        self._position_toolbar()
        logger.info("UI components initialized")
        
    def _load_plugins(self, layout):
        """Load plugin buttons into the toolbar."""
        loaded_buttons = 0
        for plugin in self.plugin_manager.get_plugins():
            try:
                button = PluginButton(plugin, self)
                layout.addWidget(button)
                loaded_buttons += 1
                logger.info(f"Added button for plugin: {plugin.name}")
            except Exception as e:
                logger.error(f"Error creating button for plugin {plugin.name}: {str(e)}")
                
        layout.addStretch()
        logger.info(f"Loaded {loaded_buttons} plugin buttons")
        
    def _position_toolbar(self):
        """Position the toolbar at the bottom of the screen."""
        desktop = QDesktopWidget().availableGeometry()
        
        # Set toolbar dimensions
        toolbar_height = 50
        toolbar_width = desktop.width()
        self.setFixedSize(toolbar_width, toolbar_height)
        
        # Position at bottom of screen
        toolbar_x = desktop.x()
        toolbar_y = desktop.height() - toolbar_height
        self.move(toolbar_x, toolbar_y)
        
        logger.info(f"Positioned toolbar at ({toolbar_x}, {toolbar_y})")
        
    def show_notification(self, message, duration=3000):
        """Show a notification message."""
        if self.notification_widget:
            self.notification_widget.show_message(message, duration)
            
    def force_show(self):
        """Force the toolbar to show and stay visible."""
        self.show()
        self.raise_()
        self.activateWindow()
