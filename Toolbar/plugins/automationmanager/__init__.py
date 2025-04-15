"""
Automation Manager plugin for the Toolbar application.
This plugin provides script management and execution functionality.
"""

from Toolbar.core.plugin_system import Plugin
from Toolbar.plugins.automationmanager.script_manager import ScriptManager

class AutomationManagerPlugin(Plugin):
    """Automation Manager plugin."""
    
    def __init__(self):
        self.script_manager = None
    
    def initialize(self, config):
        """Initialize the Automation Manager plugin."""
        try:
            # Initialize script manager
            self.script_manager = ScriptManager(config)
        except Exception as e:
            print(f"Failed to initialize Automation Manager plugin: {e}")
    
    def cleanup(self):
        """Clean up Automation Manager plugin resources."""
        pass
    
    @property
    def name(self) -> str:
        return "Automation Manager"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Provides script management and execution functionality."
