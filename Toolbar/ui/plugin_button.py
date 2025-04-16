"""
Plugin button implementation.
"""
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

class PluginButton(QPushButton):
    """Button for plugin actions in the toolbar."""
    
    def __init__(self, plugin, parent=None):
        """Initialize plugin button."""
        super().__init__(parent)
        
        # Set button properties
        self.plugin = plugin
        self.setText(plugin.name)
        
        # Handle icon
        icon = plugin.get_icon()
        if isinstance(icon, str):
            # If icon is a path string, create QIcon from it
            if icon.startswith(":"):
                # Qt resource path
                self.setIcon(QIcon(icon))
            else:
                # File path
                self.setIcon(QIcon.fromTheme(icon) or QIcon(icon))
        elif isinstance(icon, QIcon):
            # If already a QIcon, use directly
            self.setIcon(icon)
            
        # Set tooltip
        if hasattr(plugin, 'description'):
            self.setToolTip(plugin.description)
            
        # Connect click handler
        self.clicked.connect(self._handle_click)
        
        # Style settings
        self.setFixedSize(40, 40)  # Square button
        self.setIconSize(self.size() * 0.7)  # Icon size 70% of button
        
    def _handle_click(self):
        """Handle button click by activating plugin."""
        try:
            self.plugin.activate()
        except Exception as e:
            # Log error and potentially show notification
            print(f"Error activating plugin {self.plugin.name}: {str(e)}")
