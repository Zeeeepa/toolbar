"""
Linear integration plugin for the Toolbar application.
"""

from PyQt5.QtGui import QIcon
from Toolbar.core.plugin_system import Plugin, PluginType

class LinearPlugin(Plugin):
    """Plugin for Linear integration."""
    
    def __init__(self):
        super().__init__()
        self._name = "Linear Integration"
        self._version = "1.0.0"
        self._description = "Linear integration and notifications"
    
    def initialize(self, config, event_bus=None, toolbar=None):
        """Initialize the plugin."""
        super().initialize(config, event_bus, toolbar)
        return True
    
    def get_icon(self):
        """Get the plugin icon."""
        return QIcon.fromTheme("linear")
    
    def get_title(self):
        """Get the plugin title."""
        return "Linear"
