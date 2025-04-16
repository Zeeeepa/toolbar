from typing import Any, Dict, List, Optional
import logging
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QIcon, QScreen

from .notification_widget import NotificationWidget
from .plugin_button import PluginButton
from .toolbar_settings import SettingsDialog
from .plugin_manager import PluginManagerDialog

logger = logging.getLogger(__name__)

class ToolbarUI(QMainWindow):
    """Main toolbar window with plugin support."""

    def __init__(self, config: Any, plugin_manager: Any):
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

        # Add system buttons on the left
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.show_settings)
        layout.addWidget(self.settings_button)

        self.plugin_manager_button = QPushButton("Plugins")
        self.plugin_manager_button.clicked.connect(self.show_plugin_manager)
        layout.addWidget(self.plugin_manager_button)

        # Add plugin buttons
        self._load_plugins()

        # Add notification widget on the right
        layout.addWidget(self.notification_widget)

        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.create_tray_menu()
        self.tray_icon.show()
        logger.info("System tray icon created")

        # Position the toolbar at the bottom of the screen
        self.position_toolbar()
        logger.info("UI components initialized")

    def _load_plugins(self) -> None:
        """Load and add plugin buttons."""
        try:
            layout = self.centralWidget().layout()
            for plugin in self.plugin_manager.get_all_plugins():
                if not plugin.is_active():
                    continue
                try:
                    button = PluginButton(plugin, self)
                    layout.addWidget(button)
                    logger.info(f"Added button for plugin: {plugin.name}")
                except Exception as e:
                    logger.error(f"Error creating button for plugin {plugin.name}: {str(e)}")
                    logger.error(str(e), exc_info=True)
            logger.info(f"Loaded {len(self.plugin_manager.get_all_plugins())} plugin buttons")
        except Exception as e:
            logger.error(f"Error loading plugins: {str(e)}")
            logger.error(str(e), exc_info=True)

    def position_toolbar(self) -> None:
        """Position the toolbar at the bottom of the screen."""
        try:
            screen = QScreen.virtualGeometry(QApplication.primaryScreen())
            toolbar_height = 40
            toolbar_width = screen.width()
            toolbar_x = 0
            toolbar_y = screen.height() - toolbar_height

            self.setGeometry(toolbar_x, toolbar_y, toolbar_width, toolbar_height)
            logger.info(f"Positioned toolbar at ({toolbar_x}, {toolbar_y})")
        except Exception as e:
            logger.error(f"Error positioning toolbar: {str(e)}")
            logger.error(str(e), exc_info=True)

    def create_tray_menu(self) -> None:
        """Create the system tray menu."""
        menu = QMenu()
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)

        plugins_action = QAction("Plugins", self)
        plugins_action.triggered.connect(self.show_plugin_manager)
        menu.addAction(plugins_action)

        menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)

    def show_settings(self) -> None:
        """Show the settings dialog."""
        try:
            settings_dialog = SettingsDialog(self.config)
            settings_dialog.exec_()
        except Exception as e:
            logger.error(f"Error showing settings: {str(e)}")
            logger.error(str(e), exc_info=True)

    def show_plugin_manager(self) -> None:
        """Show the plugin manager dialog."""
        try:
            plugin_manager_dialog = PluginManagerDialog(self.plugin_manager)
            plugin_manager_dialog.exec_()
        except Exception as e:
            logger.error(f"Error showing plugin manager: {str(e)}")
            logger.error(str(e), exc_info=True)

    def closeEvent(self, event: Any) -> None:
        """Handle window close event."""
        self.tray_icon.hide()
        event.accept()
