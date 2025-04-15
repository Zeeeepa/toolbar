"""
Linear integration plugin for the Toolbar application.
"""

from Toolbar.core.plugin_system import Plugin
from .linear_integration import LinearIntegration

class LinearPlugin(Plugin):
    """Linear integration plugin."""
    
    def __init__(self):
        self.integration = None
    
    def initialize(self, config):
        """Initialize the Linear plugin."""
        try:
            # Initialize Linear integration
            self.integration = LinearIntegration(config)
        except Exception as e:
            print(f"Failed to initialize Linear plugin: {e}")
    
    def cleanup(self):
        """Clean up Linear plugin resources."""
        if self.integration:
            self.integration.cleanup()
    
    @property
    def name(self) -> str:
        return "Linear Integration"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Provides Linear issue tracking and project management integration."
