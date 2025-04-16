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
        
        # Handle icon loading
        icon = plugin.get_icon()
        if isinstance(icon, str):
            # If icon is a string path, convert to QIcon
            self.setIcon(QIcon(icon))
        elif isinstance(icon, QIcon):
            # If already a QIcon, use directly
            self.setIcon(icon)
        else:
            # Default icon if none provided
            self.setText(plugin.name[0])
            
        self.setIconSize(self.size() * 0.7)
        
        # Style the button
        self.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: none;
                border-radius: 5px;
                padding: 5px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #1d1d1d;
            }
        """)
        
        # Connect click handler
        self.clicked.connect(self._handle_click)
        
    def _handle_click(self):
        """Handle button click by activating the plugin"""
        try:
            self.plugin.activate()
        except Exception as e:
            print(f"Error activating plugin {self.plugin.name}: {e}")
