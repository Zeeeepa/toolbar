"""
Plugin system for the Toolbar application.
This module provides the base classes and interfaces for creating plugins.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type, Tuple
import importlib
import pkgutil
import os
import sys
import logging
import traceback
import importlib.util

# Set up logging
logger = logging.getLogger(__name__)

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
        self.failed_plugins: Dict[str, str] = {}  # Track failed plugins and their error messages
    
    def add_plugin_directory(self, directory: str) -> None:
        """Add a directory to search for plugins."""
        if os.path.isdir(directory) and directory not in self.plugin_dirs:
            self.plugin_dirs.append(directory)
    
    def _safe_import_module(self, module_name: str) -> Tuple[Optional[object], Optional[str]]:
        """
        Safely import a module and return it, or an error message if it fails.
        
        Args:
            module_name: The name of the module to import
            
        Returns:
            Tuple of (module, error_message)
            If successful, module is the imported module and error_message is None
            If failed, module is None and error_message contains the error
        """
        try:
            module = importlib.import_module(module_name)
            return module, None
        except Exception as e:
            error_msg = f"Failed to import module {module_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg
    
    def load_plugins(self) -> None:
        """Load all plugins from the configured directories."""
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                logger.warning(f"Plugin directory does not exist: {plugin_dir}")
                continue
                
            # Add the plugin directory to Python path
            if plugin_dir not in sys.path:
                sys.path.append(plugin_dir)
            
            # Find all Python modules in the directory
            for finder, name, ispkg in pkgutil.iter_modules([plugin_dir]):
                if not ispkg:
                    continue  # Skip non-package modules
                
                # Safely import the module
                module_name = f"Toolbar.plugins.{name}"
                module, error = self._safe_import_module(module_name)
                
                if error:
                    self.failed_plugins[name] = error
                    continue
                
                if not module:
                    continue
                
                # Look for Plugin subclasses in the module
                plugin_classes = []
                for item_name in dir(module):
                    try:
                        item = getattr(module, item_name)
                        if (isinstance(item, type) and 
                            issubclass(item, Plugin) and 
                            item != Plugin):
                            plugin_classes.append(item)
                    except Exception as e:
                        logger.warning(f"Error checking if {item_name} is a Plugin subclass: {e}")
                
                if not plugin_classes:
                    logger.warning(f"No Plugin subclasses found in {name}")
                    continue
                
                # Initialize each plugin class found
                for plugin_class in plugin_classes:
                    try:
                        logger.info(f"Initializing plugin: {plugin_class.__name__}")
                        plugin = plugin_class()
                        plugin.initialize(self.config)
                        self.plugins[plugin.name] = plugin
                        logger.info(f"Successfully loaded plugin: {plugin.name} v{plugin.version}")
                    except Exception as e:
                        error_msg = f"Failed to initialize plugin {plugin_class.__name__}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        self.failed_plugins[plugin_class.__name__] = error_msg
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, Plugin]:
        """Get all loaded plugins."""
        return self.plugins.copy()
    
    def get_failed_plugins(self) -> Dict[str, str]:
        """Get all plugins that failed to load and their error messages."""
        return self.failed_plugins.copy()
    
    def cleanup(self) -> None:
        """Clean up all loaded plugins."""
        for plugin in self.plugins.values():
            try:
                logger.info(f"Cleaning up plugin: {plugin.name}")
                plugin.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up plugin {plugin.name}: {e}", exc_info=True)
        self.plugins.clear()
