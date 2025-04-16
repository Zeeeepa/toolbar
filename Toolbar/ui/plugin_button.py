from PyQt5.QtWidgets import QPushButton, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import logging
import os

logger = logging.getLogger(__name__)

class PluginButton(QPushButton):
    """Button for plugin actions in the toolbar."""
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.init_ui()
        
    def init_ui(self):
        """Initialize the button UI."""
        try:
            # Set icon if available
            icon = self.plugin.get_icon()
            if icon and isinstance(icon, QIcon):
                self.setIcon(icon)
            else:
                # Use default icon
                default_icon = os.path.join(os.path.dirname(__file__), "icons/plugin.svg")
                if os.path.exists(default_icon):
                    self.setIcon(QIcon(default_icon))
            
            # Set tooltip
            tooltip = f"{self.plugin.name} v{self.plugin.version}"
            if self.plugin.description:
                tooltip += f"\n{self.plugin.description}"
            self.setToolTip(tooltip)
            
            # Set context menu
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._show_context_menu)
            
            # Connect click handler
            self.clicked.connect(self._handle_click)
            
            logger.info(f"Initialized button for plugin: {self.plugin.name}")
        except Exception as e:
            logger.error(f"Error initializing button for plugin {self.plugin.name}: {str(e)}")
            
    def _show_context_menu(self, pos):
        """Show the context menu."""
        try:
            menu = QMenu(self)
            
            # Add plugin info
            info_action = QAction(f"{self.plugin.name} v{self.plugin.version}", self)
            info_action.setEnabled(False)
            menu.addAction(info_action)
            menu.addSeparator()
            
            # Add plugin actions
            if hasattr(self.plugin, "get_actions"):
                actions = self.plugin.get_actions()
                if actions:
                    for action in actions:
                        menu_action = QAction(action["name"], self)
                        menu_action.triggered.connect(action["callback"])
                        menu.addAction(menu_action)
                    menu.addSeparator()
            
            # Add settings action if available
            if hasattr(self.plugin, "show_settings"):
                settings_action = QAction("Settings", self)
                settings_action.triggered.connect(self.plugin.show_settings)
                menu.addAction(settings_action)
            
            menu.exec_(self.mapToGlobal(pos))
        except Exception as e:
            logger.error(f"Error showing context menu for plugin {self.plugin.name}: {str(e)}")
            
    def _handle_click(self):
        """Handle button click."""
        try:
            if hasattr(self.plugin, "on_click"):
                self.plugin.on_click()
        except Exception as e:
            logger.error(f"Error handling click for plugin {self.plugin.name}: {str(e)}")
            
    def enterEvent(self, event):
        """Handle mouse enter event."""
        self.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse leave event."""
        self.setStyleSheet("")
        super().leaveEvent(event)
