"""
Linear integration plugin for the Toolbar application.
"""

from PyQt5.QtGui import QIcon
from Toolbar.core.plugin_system import Plugin

class LinearPlugin(Plugin):
    """Linear integration plugin."""
    
    def __init__(self):
        super().__init__()
        self._name = "Linear Integration"
        self._description = "Integrates with Linear for issue tracking"
        self._version = "1.0.0"
        self._icon = None
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        self._name = value
    
    def get_icon(self):
        if not self._icon:
            # Return QIcon object instead of string path
            self._icon = QIcon("Toolbar/plugins/linear/assets/linear.png")
        return self._icon
    
    def initialize(self, config):
        """Initialize the Linear plugin."""
        try:
            from .linear_integration import LinearIntegration
            self.integration = LinearIntegration(config)
            return True
        except ImportError:
            return False
    
    def cleanup(self):
        """Clean up Linear plugin resources."""
        if self.integration:
            self.integration.cleanup()
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Provides Linear issue tracking and project management integration."
