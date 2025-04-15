#!/usr/bin/env python3
import os
import sys
import importlib.util
import inspect
import logging
from typing import Dict, List, Any, Optional, Type

logger = logging.getLogger(__name__)

class Plugin:
    """
    Base class for all plugins.
    All plugins must inherit from this class.
    """
    
    def initialize(self, config):
        """
        Initialize the plugin.
        
        Args:
            config: Configuration object
        """
        pass
    
    def cleanup(self):
        """Clean up resources used by the plugin."""
        pass
    
    @property
    def name(self) -> str:
        """Get the name of the plugin."""
        return self.__class__.__name__
    
    @property
    def version(self) -> str:
        """Get the version of the plugin."""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Get the description of the plugin."""
        return "No description provided."

class PluginManager:
    """
    Plugin manager for the Toolbar application.
    Handles loading, initializing, and managing plugins.
    """
    
    def __init__(self, config):
        """
        Initialize the plugin manager.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.plugins = {}
        self.plugin_dirs = []
        self.failed_plugins = {}
        
        # Add default plugin directories
        self._add_default_plugin_dirs()
    
    def _add_default_plugin_dirs(self):
        """Add default plugin directories."""
        try:
            # Add built-in plugins directory
            builtin_plugins_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")
            self.add_plugin_directory(builtin_plugins_dir)
            
            # Add user plugins directory
            user_plugins_dir = os.path.join(os.path.expanduser("~"), ".config", "toolkit", "plugins")
            self.add_plugin_directory(user_plugins_dir)
        except Exception as e:
            logger.error(f"Error adding default plugin directories: {e}", exc_info=True)
    
    def add_plugin_directory(self, directory):
        """
        Add a directory to search for plugins.
        
        Args:
            directory: Directory path
        """
        if os.path.isdir(directory) and directory not in self.plugin_dirs:
            self.plugin_dirs.append(directory)
            logger.info(f"Added plugin directory: {directory}")
    
    def load_plugins(self):
        """Load all plugins from the plugin directories."""
        for directory in self.plugin_dirs:
            self._load_plugins_from_directory(directory)
    
    def _load_plugins_from_directory(self, directory):
        """
        Load plugins from a directory.
        
        Args:
            directory: Directory path
        """
        try:
            if not os.path.isdir(directory):
                logger.warning(f"Plugin directory does not exist: {directory}")
                return
            
            logger.info(f"Loading plugins from {directory}")
            
            # Get all subdirectories
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                
                # Skip non-directories and hidden directories
                if not os.path.isdir(item_path) or item.startswith("."):
                    continue
                
                # Skip directories without an __init__.py file
                init_file = os.path.join(item_path, "__init__.py")
                if not os.path.isfile(init_file):
                    continue
                
                # Load the plugin
                self._load_plugin(item, item_path)
        except Exception as e:
            logger.error(f"Error loading plugins from {directory}: {e}", exc_info=True)
    
    def _load_plugin(self, plugin_name, plugin_path):
        """
        Load a plugin.
        
        Args:
            plugin_name: Name of the plugin
            plugin_path: Path to the plugin directory
        """
        try:
            # Check if plugin is enabled
            if not self.config.is_plugin_enabled(plugin_name):
                logger.info(f"Plugin {plugin_name} is disabled, skipping")
                return
            
            # Import the plugin module
            spec = importlib.util.spec_from_file_location(
                f"toolkit.plugins.{plugin_name}",
                os.path.join(plugin_path, "__init__.py")
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin classes
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj != Plugin):
                    plugin_classes.append(obj)
            
            if not plugin_classes:
                logger.warning(f"No plugin classes found in {plugin_name}")
                return
            
            # Initialize each plugin class
            for plugin_class in plugin_classes:
                try:
                    plugin_instance = plugin_class()
                    plugin_instance.initialize(self.config)
                    self.plugins[plugin_instance.name] = plugin_instance
                    logger.info(f"Loaded plugin: {plugin_instance.name} v{plugin_instance.version}")
                except Exception as e:
                    logger.error(f"Error initializing plugin {plugin_class.__name__}: {e}", exc_info=True)
                    self.failed_plugins[plugin_class.__name__] = str(e)
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}", exc_info=True)
            self.failed_plugins[plugin_name] = str(e)
    
    def get_plugin(self, name):
        """
        Get a plugin by name.
        
        Args:
            name: Name of the plugin
        
        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(name)
    
    def get_all_plugins(self):
        """
        Get all loaded plugins.
        
        Returns:
            Dictionary of plugin instances
        """
        return self.plugins
    
    def get_failed_plugins(self):
        """
        Get all plugins that failed to load.
        
        Returns:
            Dictionary of plugin names and error messages
        """
        return self.failed_plugins
    
    def disable_plugin(self, name):
        """
        Disable a plugin.
        
        Args:
            name: Name of the plugin
        """
        # Disable the plugin in the configuration
        self.config.disable_plugin(name)
        
        # Remove the plugin if it's loaded
        if name in self.plugins:
            try:
                self.plugins[name].cleanup()
                del self.plugins[name]
                logger.info(f"Disabled plugin: {name}")
            except Exception as e:
                logger.error(f"Error disabling plugin {name}: {e}", exc_info=True)
    
    def enable_plugin(self, name):
        """
        Enable a plugin.
        
        Args:
            name: Name of the plugin
        """
        # Enable the plugin in the configuration
        self.config.enable_plugin(name)
        
        # Reload plugins
        self.load_plugins()
    
    def cleanup(self):
        """Clean up all plugins."""
        for name, plugin in list(self.plugins.items()):
            try:
                plugin.cleanup()
                logger.info(f"Cleaned up plugin: {name}")
            except Exception as e:
                logger.error(f"Error cleaning up plugin {name}: {e}", exc_info=True)
        
        self.plugins = {}
