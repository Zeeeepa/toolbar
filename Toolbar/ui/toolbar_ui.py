from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QMenu, QAction, QSystemTrayIcon
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QIcon, QScreen, QGuiApplication
import logging

from .plugin_button import PluginButton
from .toolbar_settings import SettingsDialog
from .plugin_manager import PluginManagerDialog
from .notification_widget import NotificationWidget

logger = logging.getLogger(__name__)

class ToolbarUI(QMainWindow):
    def __init__(self, config=None, plugin_manager=None):
        super().__init__()
        self.config = config
        self.plugin_manager = plugin_manager
        self.notification_widget = None
        self.init_ui()

    def init_ui(self):
        # Set window flags for taskbar-like behavior
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create notification widget
        self.notification_widget = NotificationWidget(self)
        logger.info("Notification widget initialized")

        # Load plugins and create buttons
        self._load_plugins()

        # Create settings and plugin manager buttons
        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.show_settings)
        layout.addWidget(settings_button)

        plugins_button = QPushButton("Plugins")
        plugins_button.clicked.connect(self.show_plugin_manager)
        layout.addWidget(plugins_button)

        # Position toolbar at the bottom of the screen
        self._position_toolbar()

        # Create system tray icon
        self._create_tray_icon()

        logger.info("UI components initialized")

    def _load_plugins(self):
        """Load and create buttons for active plugins"""
        try:
            active_plugins = self.plugin_manager.get_all_plugins() if self.plugin_manager else []
            button_count = 0
            
            for plugin in active_plugins:
                try:
                    if not plugin.is_active():
                        continue
                        
                    button = PluginButton(plugin, self)
                    self.centralWidget().layout().addWidget(button)
                    button_count += 1
                    logger.info(f"Added button for plugin: {plugin.name}")
                except Exception as e:
                    logger.error(f"Error creating button for plugin {plugin.name}: {str(e)}")
                    logger.exception(e)
                    
            logger.info(f"Loaded {button_count} plugin buttons")
        except Exception as e:
            logger.error(f"Error loading plugins: {str(e)}")
            logger.exception(e)

    def _position_toolbar(self):
        """Position the toolbar at the bottom of the screen"""
        try:
            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            
            # Set toolbar dimensions
            toolbar_height = 40
            toolbar_width = screen_geometry.width()
            
            # Position at bottom of screen
            x = screen_geometry.x()
            y = screen_geometry.height() - toolbar_height
            
            # Set window geometry
            self.setGeometry(x, y, toolbar_width, toolbar_height)
            logger.info(f"Positioned toolbar at ({x}, {y})")
            
        except Exception as e:
            logger.error(f"Error positioning toolbar: {str(e)}")
            logger.exception(e)

    def _create_tray_icon(self):
        """Create the system tray icon"""
        try:
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon("icons/toolbar.png"))
            self.tray_icon.setVisible(True)
            
            # Create tray menu
            tray_menu = QMenu()
            
            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            hide_action = QAction("Hide", self)
            hide_action.triggered.connect(self.hide)
            tray_menu.addAction(hide_action)
            
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.close)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            logger.info("System tray icon created")
            
        except Exception as e:
            logger.error(f"Error creating tray icon: {str(e)}")
            logger.exception(e)

    def show_settings(self):
        """Show the settings dialog"""
        try:
            settings_dialog = SettingsDialog(self.config, self)
            settings_dialog.exec_()
            logger.info("Settings dialog shown")
        except Exception as e:
            logger.error(f"Error showing settings: {str(e)}")
            logger.exception(e)

    def show_plugin_manager(self):
        """Show the plugin manager dialog"""
        try:
            plugin_manager_dialog = PluginManagerDialog(self.plugin_manager, self)
            plugin_manager_dialog.exec_()
            logger.info("Plugin manager dialog shown")
        except Exception as e:
            logger.error(f"Error showing plugin manager: {str(e)}")
            logger.exception(e)

    def show(self):
        """Show the toolbar"""
        super().show()
        self._position_toolbar()

    def hide(self):
        """Hide the toolbar"""
        super().hide()

    def closeEvent(self, event):
        """Handle close event"""
        self.tray_icon.hide()
        event.accept()
