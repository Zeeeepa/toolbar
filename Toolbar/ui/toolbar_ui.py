from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSystemTrayIcon, QMenu
from PyQt5.QtCore import Qt, QPoint, QRect, QSize
from PyQt5.QtGui import QIcon, QScreen, QGuiApplication
import logging
import os

from .plugin_button import PluginButton
from .toolbar_settings import SettingsDialog
from .plugin_manager import PluginManagerDialog
from .notification_widget import NotificationWidget

logger = logging.getLogger(__name__)

class ToolbarUI(QWidget):
    """Main toolbar UI class."""
    
    def __init__(self, config=None, plugin_manager=None):
        super().__init__()
        self.config = config
        self.plugin_manager = plugin_manager
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
        
        # Create main layout
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        
        # Add plugin buttons
        self._load_plugins()
        
        # Add settings button
        self.settings_button = QPushButton()
        self.settings_button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons/settings.svg")))
        self.settings_button.clicked.connect(self.show_settings)
        self.layout.addWidget(self.settings_button)
        
        # Add notification widget
        self.notification_widget = NotificationWidget(self)
        self.layout.addWidget(self.notification_widget)
        
        # Position toolbar at bottom of screen
        self._position_toolbar()
        
        # Create system tray icon
        self._create_tray_icon()
        
        logger.info("UI components initialized")

    def _load_plugins(self):
        """Load plugin buttons."""
        try:
            for plugin in self.plugin_manager.get_all_plugins():
                try:
                    button = PluginButton(plugin, self)
                    self.layout.addWidget(button)
                    logger.info(f"Added button for plugin: {plugin.name}")
                except Exception as e:
                    logger.error(f"Error creating button for plugin {plugin.name}: {str(e)}")
            
            logger.info(f"Loaded {self.layout.count()} plugin buttons")
        except Exception as e:
            logger.error(f"Error loading plugins: {str(e)}")

    def _position_toolbar(self):
        """Position the toolbar at the bottom of the screen."""
        # Get primary screen
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # Calculate toolbar dimensions
        toolbar_height = 40  # Fixed height
        toolbar_width = screen_geometry.width()  # Full screen width
        
        # Position at bottom of screen
        x = screen_geometry.x()
        y = screen_geometry.height() - toolbar_height
        
        # Set geometry
        self.setGeometry(x, y, toolbar_width, toolbar_height)
        logger.info(f"Positioned toolbar at ({x}, {y})")

    def _create_tray_icon(self):
        """Create the system tray icon."""
        try:
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons/notification.svg")))
            
            # Create tray menu
            tray_menu = QMenu()
            settings_action = tray_menu.addAction("Settings")
            settings_action.triggered.connect(self.show_settings)
            plugins_action = tray_menu.addAction("Plugins")
            plugins_action.triggered.connect(self.show_plugin_manager)
            quit_action = tray_menu.addAction("Quit")
            quit_action.triggered.connect(self.close)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
            logger.info("System tray icon created")
        except Exception as e:
            logger.error(f"Error creating system tray icon: {str(e)}")

    def show_settings(self):
        """Show the settings dialog."""
        try:
            dialog = SettingsDialog(self.config, self)
            dialog.exec_()
            logger.info("Settings dialog shown")
        except Exception as e:
            logger.error(f"Error showing settings dialog: {str(e)}")

    def show_plugin_manager(self):
        """Show the plugin manager dialog."""
        try:
            dialog = PluginManagerDialog(self.plugin_manager, self)
            dialog.exec_()
            logger.info("Plugin manager dialog shown")
        except Exception as e:
            logger.error(f"Error showing plugin manager dialog: {str(e)}")

    def closeEvent(self, event):
        """Handle close event."""
        self.tray_icon.hide()
        event.accept()
