from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QPushButton,
                           QMenu, QAction, QSystemTrayIcon, QApplication)
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QIcon, QScreen
import logging

from .plugin_button import PluginButton
from .toolbar_settings import SettingsDialog
from .plugin_manager import PluginManagerDialog
from .notification_widget import NotificationWidget

logger = logging.getLogger(__name__)

class ToolbarUI(QMainWindow):
    def __init__(self, plugin_manager=None):
        super().__init__()
        self.plugin_manager = plugin_manager
        self.notification_widget = None
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Toolbar")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QHBoxLayout(central_widget)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)

        # Add settings button
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.show_settings)
        self.layout.addWidget(self.settings_btn)

        # Add plugins button
        self.plugins_btn = QPushButton("Plugins")
        self.plugins_btn.clicked.connect(self.show_plugin_manager)
        self.layout.addWidget(self.plugins_btn)

        # Load plugin buttons
        self._load_plugins()

        # Add spacer to push buttons to the left
        self.layout.addStretch()

        # Initialize notification widget
        self.notification_widget = NotificationWidget(self)
        logger.info("Notification widget initialized")

        # Set up system tray
        self._setup_system_tray()

        # Position toolbar at bottom of screen
        self._position_toolbar()

    def _load_plugins(self):
        """Load plugin buttons"""
        if not self.plugin_manager:
            return

        loaded_buttons = 0
        for plugin in self.plugin_manager.get_plugins():
            try:
                button = PluginButton(plugin, self)
                self.layout.addWidget(button)
                loaded_buttons += 1
            except Exception as e:
                logger.error(f"Error creating button for plugin {plugin.name}: {str(e)}")
                continue

        logger.info(f"Loaded {loaded_buttons} plugin buttons")

    def _setup_system_tray(self):
        """Set up system tray icon and menu"""
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

    def _position_toolbar(self):
        """Position the toolbar at the bottom of the screen"""
        screen = QApplication.primaryScreen()
        if not screen:
            return
            
        geometry = screen.availableGeometry()
        toolbar_height = 40
        self.setGeometry(0, geometry.height() - toolbar_height, geometry.width(), toolbar_height)

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        dialog.exec_()

    def show_plugin_manager(self):
        """Show plugin manager dialog"""
        dialog = PluginManagerDialog(self)
        dialog.exec_()

    def show_notification(self, message, duration=3000):
        """Show notification message"""
        if self.notification_widget:
            self.notification_widget.show_message(message, duration)

    def force_show(self):
        """Force show the toolbar"""
        self.show()
        self.raise_()
        self.activateWindow()
        
        # Log current state
        logger.info(f"Force showing toolbar. Current geometry: {self.geometry().x()}, {self.geometry().y()}, {self.geometry().width()}x{self.geometry().height()}")
        logger.info(f"Current window flags: {self.windowFlags()}")
        logger.info(f"Current opacity: {self.windowOpacity()}")
        
        # Ensure proper positioning
        self._position_toolbar()
        logger.info(f"Toolbar position after force show: {self.geometry().x()}, {self.geometry().y()}, {self.geometry().width()}x{self.geometry().height()}")
