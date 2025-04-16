from PyQt5.QtWidgets import QPushButton, QSizePolicy
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

class PluginButton(QPushButton):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        
        # Set button properties
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(40, 40)
        self.setToolTip(plugin.name)
        
        # Handle icon setting
        icon = plugin.get_icon()
        if isinstance(icon, str):
            # If icon is a string path, convert to QIcon
            self.setIcon(QIcon(icon))
        elif isinstance(icon, QIcon):
            # If already a QIcon, use directly
            self.setIcon(icon)
        
        # Set button style
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
        # Connect click handler
        self.clicked.connect(self.handle_click)
    
    def handle_click(self):
        """Handle button click by activating the plugin"""
        if hasattr(self.plugin, 'activate'):
            self.plugin.activate()
