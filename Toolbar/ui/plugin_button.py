"""
Plugin button implementation.
"""
import logging
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from ..core.enhanced_plugin_system import EnhancedPlugin

logger = logging.getLogger(__name__)

class PluginButton(QPushButton):
    """Button for plugin actions in the toolbar."""
    
    def __init__(self, plugin: EnhancedPlugin, parent=None):
        """Initialize plugin button."""
        super().__init__(parent)
        
        self.plugin = plugin
        
        # Set button text
        self.setText(plugin.name)
        
        # Set icon if available
        icon = plugin.get_icon()
        if icon:
            if isinstance(icon, str):
                # Convert string path to QIcon
                self.setIcon(QIcon(icon))
            elif isinstance(icon, QIcon):
                self.setIcon(icon)
            else:
                logger.warning(f"Invalid icon type for plugin {plugin.name}: {type(icon)}")
        
        # Set tooltip
        if plugin.description:
            self.setToolTip(plugin.description)
            
        # Connect click handler
        self.clicked.connect(self._handle_click)
        
        # Set size policy
        self.setSizePolicy(Qt.ExpandingPolicy, Qt.FixedPolicy)
        
    def _handle_click(self):
        """Handle button click."""
        try:
            self.plugin.handle_click()
        except Exception as e:
            logger.error(f"Error handling click for plugin {self.plugin.name}: {str(e)}")
            logger.error("Traceback:", exc_info=True)
