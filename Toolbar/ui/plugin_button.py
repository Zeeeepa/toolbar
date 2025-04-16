from PyQt5.QtWidgets import QPushButton, QSizePolicy
from PyQt5.QtGui import QIcon
import logging

logger = logging.getLogger(__name__)

class PluginButton(QPushButton):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.init_ui()

    def init_ui(self):
        """Initialize the button UI"""
        # Set button text
        self.setText(self.plugin.name)
        
        # Set icon if available
        icon = self.plugin.get_icon()
        if icon:
            if isinstance(icon, str):
                # Convert string path to QIcon
                self.setIcon(QIcon(icon))
            else:
                self.setIcon(icon)
        
        # Set tooltip
        tooltip = self.plugin.get_description() or self.plugin.name
        self.setToolTip(tooltip)
        
        # Connect click handler
        self.clicked.connect(self._handle_click)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
    def _handle_click(self):
        """Handle button click"""
        try:
            self.plugin.on_click()
        except Exception as e:
            logger.error(f"Error handling click for plugin {self.plugin.name}: {str(e)}")
            if hasattr(self.parent(), 'show_notification'):
                self.parent().show_notification(f"Error in plugin {self.plugin.name}: {str(e)}")
