import logging
import sys
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QMenu, QAction,
                           QSystemTrayIcon, QApplication, QDialog)
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QIcon, QScreen

from .plugin_button import PluginButton
from .toolbar_settings import SettingsDialog
from .plugin_manager import PluginManagerDialog
from .notification_widget import NotificationWidget

logger = logging.getLogger(__name__)

class ToolbarUI(QWidget):
    def __init__(self, config=None, plugin_manager=None):
        super().__init__()
        self.config = config
        self.plugin_manager = plugin_manager
        self.notification_widget = NotificationWidget()
        self.init_ui()

    def init_ui(self):
        logger.info("Initializing UI components")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Create main layout
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        
        # Add settings and plugin manager buttons on the left
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.show_settings)
        self.layout.addWidget(self.settings_button)
        
        self.plugin_manager_button = QPushButton("Plugins")
        self.plugin_manager_button.clicked.connect(self.show_plugin_manager)
        self.layout.addWidget(self.plugin_manager_button)
        
        # Add plugin buttons
        self._load_plugins()
        
        # Add notification widget on the right
        self.layout.addStretch()
        self.layout.addWidget(self.notification_widget)
        
        # Set up system tray
        self.setup_system_tray()
        
        # Position toolbar at bottom of screen
        self.position_toolbar()
        logger.info("UI components initialized")

    def _load_plugins(self):
        logger.info("Loading plugin buttons")
        if not self.plugin_manager:
            return
            
        for plugin in self.plugin_manager.get_active_plugins():
            try:
                button = PluginButton(plugin, self)
                self.layout.addWidget(button)
                logger.info(f"Added button for plugin: {plugin.name}")
            except Exception as e:
                logger.error(f"Error creating button for plugin {plugin.name}: {str(e)}")
                logger.error(str(e), exc_info=True)

        logger.info(f"Loaded {len(self.plugin_manager.get_active_plugins())} plugin buttons")

    def setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        self.tray_menu.addAction(show_action)
        
        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)
        self.tray_menu.addAction(hide_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        self.tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
        logger.info("System tray icon created")

    def position_toolbar(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # Set toolbar width to screen width
        toolbar_width = screen_geometry.width()
        toolbar_height = 40  # Fixed height
        
        # Position at bottom of screen
        x = 0
        y = screen_geometry.height() - toolbar_height
        
        self.setGeometry(x, y, toolbar_width, toolbar_height)
        logger.info(f"Positioned toolbar at ({x}, {y})")

    def show_settings(self):
        try:
            settings_dialog = SettingsDialog(self)
            settings_dialog.exec_()
        except Exception as e:
            logger.error(f"Error showing settings: {str(e)}")
            logger.error(str(e), exc_info=True)

    def show_plugin_manager(self):
        try:
            plugin_manager_dialog = PluginManagerDialog(self)
            plugin_manager_dialog.exec_()
        except Exception as e:
            logger.error(f"Error showing plugin manager: {str(e)}")
            logger.error(str(e), exc_info=True)

    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()
