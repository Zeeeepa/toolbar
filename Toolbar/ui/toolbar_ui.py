"""
Toolbar UI implementation.
"""
import logging
import os
from typing import Dict, Optional

from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QPushButton,
    QSystemTrayIcon, QMenu, QAction, QDesktopWidget,
    QDialog, QToolBar, QLabel
)

from ..core.config import Config
from ..core.enhanced_plugin_system import EnhancedPlugin
from .notification_widget import NotificationWidget
from .plugin_button import PluginButton
from .toolbar_settings import SettingsDialog
from .plugin_manager import PluginManagerDialog

logger = logging.getLogger(__name__)

class ToolbarUI(QMainWindow):
    """
    Enhanced toolbar window with plugin management.
    This class provides a robust interface for the toolbar application.
    """
    
    def __init__(self, config, plugin_manager, parent=None):
        """
        Initialize the toolbar.
        
        Args:
            config: Configuration object
            plugin_manager: Plugin manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config
        self.plugin_manager = plugin_manager
        self.plugin_buttons = {}
        self.plugin_menus = {}
        self.tray_icon = None
        
        # Set window properties
        self.setWindowTitle("Toolbar")
        
        # Get position and opacity from config
        self.position = self.config.get_setting("ui.position", "bottom")  # Default to bottom like Windows taskbar
        self.opacity = float(self.config.get_setting("ui.opacity", 1.0))  # Default to fully opaque
        self.stay_on_top = self.config.get_setting("ui.stay_on_top", True)
        
        # Set window flags based on configuration
        self._update_window_flags()
        
        # Set window opacity
        self.setWindowOpacity(self.opacity)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Set the background color to match Windows taskbar
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(32, 32, 32))  # Dark gray like Windows taskbar
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))  # White text
        self.setPalette(palette)
        
        # Create main layout based on position
        self._create_layout()
        
        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        
        # Style the toolbar to match Windows taskbar
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #202020;
                border: none;
                spacing: 4px;
                padding: 2px;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QToolButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
        # Add toolbar to appropriate position
        if self.position in ['top', 'bottom']:
            self.addToolBar(Qt.TopToolBarArea if self.position == 'top' else Qt.BottomToolBarArea, self.toolbar)
        else:
            self.addToolBar(Qt.LeftToolBarArea if self.position == 'left' else Qt.RightToolBarArea, self.toolbar)
        
        # Create status bar
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Style the status bar
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #202020;
                color: white;
                border: none;
            }
            QLabel {
                color: white;
            }
        """)
        
        # Initialize UI components
        self._init_ui()
        
        # Load plugins
        self._load_plugins()
        
        # Position the toolbar
        self._position_toolbar()
        
        # Set up auto-save timer
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(60000)  # Save every minute
        
        # Create system tray icon if enabled
        if self.config.get_setting("ui.minimize_to_tray", True):
            self._create_tray_icon()
        
        logger.info("Toolbar initialized")

    def _update_window_flags(self):
        """Update window flags based on configuration."""
        flags = Qt.Tool | Qt.FramelessWindowHint  # Base flags for toolbar-like window
        
        if self.stay_on_top:
            flags |= Qt.WindowStaysOnTopHint
        
        self.setWindowFlags(flags)
    
    def _position_toolbar(self):
        """Position the toolbar on the screen."""
        try:
            # Get screen geometry
            screen = QDesktopWidget().screenGeometry()
            
            # Set size based on position
            if self.position in ['top', 'bottom']:
                width = screen.width()
                height = 40  # Fixed height like Windows taskbar
                x = 0
                y = screen.height() - height if self.position == 'bottom' else 0
            else:
                width = 40  # Fixed width for vertical orientation
                height = screen.height()
                x = screen.width() - width if self.position == 'right' else 0
                y = 0
            
            # Set geometry
            self.setGeometry(x, y, width, height)
            
            logger.info(f"Positioned toolbar at ({x}, {y})")
        except Exception as e:
            logger.error(f"Error positioning toolbar: {e}", exc_info=True)
            raise

    def _create_layout(self):
        """Create the main layout for the toolbar."""
        layout = QHBoxLayout()
        self.central_widget.setLayout(layout)
        
    def _init_ui(self):
        """Initialize the UI components."""
        # Set window flags
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |  # Always on top
            Qt.FramelessWindowHint |   # No window frame
            Qt.Tool                    # No taskbar icon
        )

        # Create horizontal layout
        layout = QHBoxLayout()
        self.central_widget.setLayout(layout)
        
        # Add settings button
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self.show_settings)
        layout.addWidget(settings_btn)
        
        # Add plugins button
        plugins_btn = QPushButton("Plugins")
        plugins_btn.clicked.connect(self.show_plugin_manager)
        layout.addWidget(plugins_btn)
        
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

    def _create_tray(self):
        """Create the system tray icon and menu."""
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
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
                logger.error(f"Traceback:", exc_info=True)
                
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
            self.centralWidget().layout().itemAt(i).widget().setParent(None)
            
        # Reload buttons
        self._load_plugins(self.centralWidget().layout())

    def show_notification(self, title: str, message: str, duration: Optional[int] = None):
        """Show a notification."""
        self.notification_widget.show_notification(title, message, duration)
