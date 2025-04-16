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

    def __init__(self, config: Config, plugins: Dict[str, EnhancedPlugin]):
        """Initialize the toolbar UI."""
        super().__init__()

        self.config = config
        self.plugins = plugins
        self.notification_widget = None
        self.settings_dialog = None
        self.plugin_manager_dialog = None
        
        # Store the original size before going fullwidth
        self.original_width = 800
        self.original_height = 40  # Reduced height to match taskbar
        
        # Initialize UI
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the UI components."""
        # Set window flags for taskbar-like behavior
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |    # Always on top
            Qt.FramelessWindowHint |     # No window frame
            Qt.WindowDoesNotAcceptFocus  # Don't take focus
        )
        
        # Set window attributes
        self.setAttribute(Qt.WA_TranslucentBackground)  # Enable transparency
        self.setAttribute(Qt.WA_ShowWithoutActivating) # Show without focus

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Set widget style
        central_widget.setStyleSheet("""
            QWidget {
                background-color: #2D2D2D;
                border: none;
            }
            QPushButton {
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                padding: 5px 10px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
            }
        """)
        
        # Create horizontal layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        central_widget.setLayout(layout)
        
        # Add settings button
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self.show_settings)
        layout.addWidget(settings_btn)
        
        # Add plugins button
        plugins_btn = QPushButton("Plugins")
        plugins_btn.clicked.connect(self.show_plugin_manager)
        layout.addWidget(plugins_btn)
        
        # Add stretch to push buttons to the left
        layout.addStretch()
        
        # Load plugin buttons
        self._load_plugins(layout)
        
        # Set initial size
        self.resize(self.original_width, self.original_height)
        
        # Position toolbar
        self._position_toolbar()
        
        # Create system tray icon
        self._create_tray()
        
        # Initialize notification widget
        self.notification_widget = NotificationWidget(self)
        logger.info("UI components initialized")

    def _position_toolbar(self):
        """Position the toolbar on the screen."""
        # Get screen geometry
        screen = QDesktopWidget().screenGeometry()
        
        # Calculate position for bottom of screen
        y = screen.height() - self.height()
        
        # Set width to full screen width
        self.setFixedWidth(screen.width())
        
        # Move to position
        self.move(0, y)
        
        logger.info(f"Positioned toolbar at ({self.x()}, {y})")

    def _create_tray(self):
        """Create the system tray icon and menu."""
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Set default icon
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "tray.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Add actions
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)
        
        plugins_action = QAction("Plugins", self)
        plugins_action.triggered.connect(self.show_plugin_manager)
        tray_menu.addAction(plugins_action)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)
        
        # Set tray icon menu
        self.tray_icon.setContextMenu(tray_menu)
        
        # Show tray icon
        self.tray_icon.show()
        
        logger.info("System tray icon created")

    def _load_plugins(self, layout):
        """Load plugin buttons into the toolbar."""
        button_count = 0
        
        for plugin_id, plugin in self.plugins.items():
            try:
                button = PluginButton(plugin, self)
                layout.addWidget(button)
                button_count += 1
                logger.info(f"Added button for plugin: {plugin_id}")
            except Exception as e:
                logger.error(f"Error creating button for plugin {plugin_id}: {str(e)}")
                logger.error("Traceback:", exc_info=True)
                
        logger.info(f"Loaded {button_count} plugin buttons")

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
            widget = self.centralWidget().layout().itemAt(i).widget()
            if widget:
                widget.setParent(None)
            
        # Reload buttons
        self._load_plugins(self.centralWidget().layout())

    def show_notification(self, title: str, message: str, duration: Optional[int] = None):
        """Show a notification."""
        self.notification_widget.show_notification(title, message, duration)
