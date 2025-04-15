"""
Toolbar - A modular taskbar application with plugin support.

This package provides a customizable toolbar application with plugin support
for GitHub, Linear, template prompts, auto-scripting, and event automation.
"""

__version__ = "1.0.0"
__author__ = "Zeeeepa"
__email__ = "info@zeeeepa.com"

# Import main components for easier access
from Toolbar.main import main
from Toolbar.core.config import Config, get_config_instance
from Toolbar.core.plugin_system import PluginManager, Plugin, PluginType, PluginState
from Toolbar.core.enhanced_plugin_system import EnhancedPluginManager
from Toolbar.ui.toolbar_ui import ToolbarUI

# Define what's available when importing from this package
__all__ = [
    'main',
    'Config', 
    'get_config_instance',
    'PluginManager', 
    'Plugin', 
    'PluginType', 
    'PluginState',
    'EnhancedPluginManager',
    'ToolbarUI'
]
