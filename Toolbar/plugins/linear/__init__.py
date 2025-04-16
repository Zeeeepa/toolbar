"""
Linear integration plugin for the Toolbar application.
"""

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget

class LinearPlugin:
    """Linear integration plugin."""
    
    def __init__(self):
        self._name = "Linear Integration"
        self._icon = None
        self._config = None
        self._event_bus = None
        self._toolbar = None
    
    @property
    def name(self):
        return self._name
    
    def get_icon(self):
        return self._icon or QIcon()
    
    def initialize(self, config, event_bus, toolbar):
        """Initialize the Linear plugin."""
        self._config = config
        self._event_bus = event_bus
        self._toolbar = toolbar
        # Initialize Linear client and handlers
        try:
            from .linear_client import setup_linear_client
            setup_linear_client(self._event_bus)
        except ImportError:
            print("Could not initialize Linear client")
    
    def cleanup(self):
        """Clean up Linear plugin resources."""
        pass
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Provides Linear issue tracking and project management integration."
