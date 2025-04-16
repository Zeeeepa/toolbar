from PyQt5.QtWidgets import QPushButton, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

class PluginButton(QPushButton):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        """Initialize the plugin button UI"""
        try:
            # Set button properties
            self.setFixedSize(32, 32)
            self.setIcon(QIcon(self.plugin.get_icon()))
            self.setToolTip(self.plugin.get_name())
            
            # Create context menu
            menu = QMenu(self)
            
            # Add plugin actions
            for action in self.plugin.get_actions():
                menu_action = QAction(action["name"], self)
                menu_action.triggered.connect(action["callback"])
                if "icon" in action:
                    menu_action.setIcon(QIcon(action["icon"]))
                menu.addAction(menu_action)
                
            # Add separator and settings
            menu.addSeparator()
            settings_action = QAction("Settings", self)
            settings_action.triggered.connect(self.plugin.show_settings)
            menu.addAction(settings_action)
            
            self.setMenu(menu)
            
        except Exception as e:
            self.parent.logger.error(f"Error initializing plugin button for {self.plugin.name}: {str(e)}")
            self.parent.logger.error(f"{str(e)}", exc_info=True)
            
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            # Show plugin menu on left click
            self.showMenu()
        else:
            super().mousePressEvent(event)
