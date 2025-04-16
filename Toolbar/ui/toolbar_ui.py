import os
import logging
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
    """Main toolbar window"""
    def __init__(self, config, plugin_manager):
        super().__init__()
        self.config = config
        self.plugin_manager = plugin_manager
        self.notification_widget = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI components"""
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create left section for system buttons
        left_section = QWidget()
        left_layout = QHBoxLayout(left_section)
        left_layout.setContentsMargins(5, 0, 5, 0)
        left_layout.setSpacing(2)

        # Add settings button
        settings_button = QPushButton()
        settings_button.setIcon(QIcon(os.path.join("Toolbar", "icons", "settings.png")))
        settings_button.clicked.connect(self.show_settings)
        left_layout.addWidget(settings_button)

        # Add plugin manager button
        plugin_button = QPushButton()
        plugin_button.setIcon(QIcon(os.path.join("Toolbar", "icons", "plugin.png")))
        plugin_button.clicked.connect(self.show_plugin_manager)
        left_layout.addWidget(plugin_button)

        layout.addWidget(left_section)

        # Create middle section for plugin buttons
        middle_section = QWidget()
        middle_layout = QHBoxLayout(middle_section)
        middle_layout.setContentsMargins(5, 0, 5, 0)
        middle_layout.setSpacing(2)
        self._load_plugins(middle_layout)
        layout.addWidget(middle_section)

        # Create right section for notifications
        right_section = QWidget()
        right_layout = QHBoxLayout(right_section)
        right_layout.setContentsMargins(5, 0, 5, 0)
        right_layout.setSpacing(2)

        # Add notification widget
        self.notification_widget = NotificationWidget()
        right_layout.addWidget(self.notification_widget)
        layout.addWidget(right_section)

        # Set window properties
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QMainWindow {
                background: rgba(30, 30, 30, 0.9);
                border: none;
            }
            QPushButton {
                background: transparent;
                border: none;
                padding: 5px;
                min-width: 30px;
                min-height: 30px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
        """)

        # Position toolbar at bottom of screen
        self._position_toolbar()

        # Create system tray icon
        self._create_tray_icon()

        logger.info("UI components initialized")

    def _load_plugins(self, layout):
        """Load plugin buttons"""
        try:
            for plugin in self.plugin_manager.get_active_plugins():
                button = PluginButton(plugin, self)
                layout.addWidget(button)
                logger.info("Added button for plugin: %s", plugin.name)
        except Exception as e:
            logger.error("Error loading plugin buttons: %s", str(e))
            logger.error(str(e), exc_info=True)

    def _position_toolbar(self):
        """Position toolbar at bottom of screen"""
        screen = QScreen.virtualGeometry(QApplication.primaryScreen())
        toolbar_height = 40
        toolbar_width = screen.width()
        toolbar_x = screen.x()
        toolbar_y = screen.height() - toolbar_height

        self.setGeometry(toolbar_x, toolbar_y, toolbar_width, toolbar_height)
        logger.info("Positioned toolbar at (%d, %d)", toolbar_x, toolbar_y)

    def _create_tray_icon(self):
        """Create system tray icon"""
        try:
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon(os.path.join("Toolbar", "icons", "tray.png")))
            self.tray_icon.setVisible(True)

            # Create tray menu
            tray_menu = QMenu()
            settings_action = QAction("Settings", self)
            settings_action.triggered.connect(self.show_settings)
            tray_menu.addAction(settings_action)

            plugins_action = QAction("Plugins", self)
            plugins_action.triggered.connect(self.show_plugin_manager)
            tray_menu.addAction(plugins_action)

            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(QApplication.quit)
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            logger.info("System tray icon created")
        except Exception as e:
            logger.error("Error creating tray icon: %s", str(e))
            logger.error(str(e), exc_info=True)

    def show_settings(self):
        """Show settings dialog"""
        try:
            settings_dialog = SettingsDialog(self.config)
            settings_dialog.exec_()
        except Exception as e:
            logger.error("Error showing settings: %s", str(e))
            logger.error(str(e), exc_info=True)

    def show_plugin_manager(self):
        """Show plugin manager dialog"""
        try:
            plugin_manager_dialog = PluginManagerDialog(self.plugin_manager)
            plugin_manager_dialog.exec_()
        except Exception as e:
            logger.error("Error showing plugin manager: %s", str(e))
            logger.error(str(e), exc_info=True)
