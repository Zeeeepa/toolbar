"""
Plugin system for the Toolbar application.
This module provides the base classes and interfaces for creating plugins.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type
import importlib
import pkgutil
import os
import sys

class Plugin(ABC):
    """Base class for all plugins."""
    
    @abstractmethod
    def initialize(self, config: 'Config') -> None:
        """Initialize the plugin with the given configuration."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up any resources used by the plugin."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the plugin."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Return the version of the plugin."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of the plugin."""
        pass

class PluginManager:
    """Manages the loading and lifecycle of plugins."""
    
    def __init__(self, config: 'Config'):
        self.config = config
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_dirs: List[str] = []
    
    def add_plugin_directory(self, directory: str) -> None:
        """Add a directory to search for plugins."""
        if os.path.isdir(directory) and directory not in self.plugin_dirs:
            self.plugin_dirs.append(directory)
    
    def load_plugins(self) -> None:
        """Load all plugins from the configured directories."""
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                continue
                
            # Add the plugin directory to Python path
            if plugin_dir not in sys.path:
                sys.path.append(plugin_dir)
            
            # Find all Python modules in the directory
            for finder, name, ispkg in pkgutil.iter_modules([plugin_dir]):
                try:
                    module = importlib.import_module(name)
                    for item_name in dir(module):
                        item = getattr(module, item_name)
                        if (isinstance(item, type) and 
                            issubclass(item, Plugin) and 
                            item != Plugin):
                            # Initialize the plugin
                            plugin = item()
                            plugin.initialize(self.config)
                            self.plugins[plugin.name] = plugin
                except Exception as e:
                    print(f"Failed to load plugin {name}: {e}")
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self.plugins.get(name)
    
    def cleanup(self) -> None:
        """Clean up all loaded plugins."""
        for plugin in self.plugins.values():
            try:
                plugin.cleanup()
            except Exception as e:
                print(f"Error cleaning up plugin {plugin.name}: {e}")
        self.plugins.clear() 