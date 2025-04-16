import logging
import os
from typing import Any, Dict, List, Optional
from PyQt5.QtCore import Qt, QPoint, QRect, QSize
from PyQt5.QtGui import QIcon, QScreen
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QSystemTrayIcon, QMenu, QAction,
    QApplication, QDesktopWidget
)

from .notification_widget import NotificationWidget
from .plugin_button import PluginButton
from .plugin_manager import PluginManagerDialog
from .toolbar_settings import SettingsDialog

logger = logging.getLogger(__name__)

class ToolbarUI(QMainWindow):
    """Main toolbar window."""

    def __init__(self, config: Any = None, plugin_manager: Any = None) -> None:
        super().__init__()
        self.config = config
        self.plugin_manager = plugin_manager
        self.notification_widget = NotificationWidget()
        logger.info("Notification widget initialized")
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the UI components."""
        # Set window flags for taskbar-like behavior
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add left section for system buttons
        left_section = QWidget()
        left_layout = QHBoxLayout(left_section)
        left_layout.setContentsMargins(5, 0, 5, 0)
        left_layout.setSpacing(2)

        # Add settings button
        settings_button = QPushButton()
        settings_button.setIcon(QIcon(os.path.join("icons", "settings.png")))
        settings_button.setToolTip("Settings")
        settings_button.clicked.connect(self.show_settings)
        left_layout.addWidget(settings_button)

        # Add plugin manager button
        plugin_button = QPushButton()
        plugin_button.setIcon(QIcon(os.path.join("icons", "plugin.png")))
        plugin_button.setToolTip("Plugin Manager")
        plugin_button.clicked.connect(self.show_plugin_manager)
        left_layout.addWidget(plugin_button)

        layout.addWidget(left_section)

        # Add spacer to push buttons to the sides
        layout.addStretch()

        # Add right section for plugin buttons
        right_section = QWidget()
        right_layout = QHBoxLayout(right_section)
        right_layout.setContentsMargins(5, 0, 5, 0)
        right_layout.setSpacing(2)

        # Load plugin buttons
        self._load_plugins(right_layout)

        layout.addWidget(right_section)

        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(os.path.join("icons", "toolbar.png")))
        self.tray_icon.setVisible(True)

        # Create tray menu
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        logger.info("System tray icon created")

        # Position the toolbar at the bottom of the screen
        self.position_toolbar()
        logger.info("UI components initialized")

    def _load_plugins(self, layout: QHBoxLayout) -> None:
        """Load plugin buttons into the toolbar."""
        if not self.plugin_manager:
            return

        try:
            for plugin in self.plugin_manager.get_active_plugins():
                try:
                    button = PluginButton(plugin, self)
                    layout.addWidget(button)
                    logger.info("Added button for plugin: %s", plugin.name)
                except Exception as e:
                    logger.error("Error creating button for plugin %s: %s", plugin.name, str(e))
                    logger.error(str(e), exc_info=True)
        except Exception as e:
            logger.error("Error loading plugin buttons: %s", str(e))
            logger.error(str(e), exc_info=True)

        logger.info("Loaded %d plugin buttons", layout.count())

    def position_toolbar(self) -> None:
        """Position the toolbar at the bottom of the screen."""
        screen = QApplication.primaryScreen()
        if not screen:
            return

        screen_geometry = screen.geometry()
        taskbar_height = 40  # Adjust this value as needed

        # Set toolbar size
        toolbar_width = screen_geometry.width()
        self.setFixedSize(toolbar_width, taskbar_height)

        # Position at bottom of screen
        x = screen_geometry.x()
        y = screen_geometry.height() - taskbar_height
        self.move(x, y)
        logger.info("Positioned toolbar at (%d, %d)", x, y)

    def show_settings(self) -> None:
        """Show the settings dialog."""
        try:
            settings_dialog = SettingsDialog(self)
            settings_dialog.exec_()
        except Exception as e:
            logger.error("Error showing settings: %s", str(e))
            logger.error(str(e), exc_info=True)

    def show_plugin_manager(self) -> None:
        """Show the plugin manager dialog."""
        try:
            plugin_manager_dialog = PluginManagerDialog(self)
            plugin_manager_dialog.exec_()
        except Exception as e:
            logger.error("Error showing plugin manager: %s", str(e))
            logger.error(str(e), exc_info=True)

    def show_notification(self, title: str, message: str) -> None:
        """Show a notification."""
        self.notification_widget.show_notification(title, message)
