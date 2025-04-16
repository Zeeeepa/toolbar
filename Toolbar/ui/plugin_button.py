"""
Plugin button implementation.
"""
import logging
import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QPushButton

from ..core.enhanced_plugin_system import EnhancedPlugin

logger = logging.getLogger(__name__)

class PluginButton(QPushButton):
    """Button for plugin actions."""
    
    def __init__(self, plugin: EnhancedPlugin, parent=None):
        """Initialize plugin button."""
        super().__init__(parent)
        
        self.plugin = plugin
        self._init_button()
        
    def _init_button(self):
        """Initialize button appearance and behavior."""
        # Set icon if available
        icon = self._get_plugin_icon()
        if icon:
            self.setIcon(icon)
        else:
            # Fallback to text if no icon
            self.setText(self.plugin.name)
            
        # Set tooltip
        self.setToolTip(self.plugin.description or self.plugin.name)
        
        # Connect click handler
        self.clicked.connect(self._handle_click)
        
        # Set button style
        self.setFlat(True)  # Make button flat for taskbar-like appearance
        
    def _get_plugin_icon(self) -> Optional[QIcon]:
        """Get plugin icon, with fallbacks."""
        try:
            # Try plugin's get_icon method first
            icon = self.plugin.get_icon()
            if isinstance(icon, str):
                # If string path returned, convert to QIcon
                if os.path.exists(icon):
                    return QIcon(icon)
                else:
                    logger.warning(f"Icon path not found: {icon}")
            elif isinstance(icon, QIcon):
                return icon
                
            # Try plugin's icon directory
            plugin_icon = os.path.join(
                os.path.dirname(self.plugin.__class__.__module__),
                "icons",
                "icon.png"
            )
            if os.path.exists(plugin_icon):
                return QIcon(plugin_icon)
                
        except Exception as e:
            logger.error(f"Error getting icon for plugin {self.plugin.name}: {str(e)}")
            
        return None
        
    def _handle_click(self):
        """Handle button click."""
        try:
            self.plugin.handle_click()
        except Exception as e:
            logger.error(f"Error handling click for plugin {self.plugin.name}: {str(e)}")
            logger.error("Traceback:", exc_info=True)
