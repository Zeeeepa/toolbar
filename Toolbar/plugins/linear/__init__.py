"""
Linear integration plugin for the Toolbar application.
"""

from PyQt5.QtGui import QIcon
import os

class LinearPlugin:
    """Linear integration plugin."""
    
    def __init__(self):
        self._name = "Linear Integration"
        self._version = "1.0.0"
        self._description = "Linear integration plugin"
        self._config = None
        self._event_bus = None
        self._toolbar = None
        self._active = False
    
    @property
    def name(self):
        return self._name
    
    @property
    def version(self):
        return self._version
    
    @property
    def description(self):
        return self._description
    
    def initialize(self, config, event_bus, toolbar):
        """Initialize the Linear plugin."""
        self._config = config
        self._event_bus = event_bus
        self._toolbar = toolbar
        self._active = True
    
    def is_active(self):
        return self._active
    
    def get_icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icons/linear.png")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        return None
    
    def get_actions(self):
        return [
            {
                "name": "Open Linear",
                "callback": self.open_linear
            },
            {
                "name": "View Issues",
                "callback": self.view_issues
            }
        ]
    
    def handle_click(self):
        self.open_linear()
    
    def open_linear(self):
        # Open Linear in browser
        pass
    
    def view_issues(self):
        # View Linear issues
        pass
