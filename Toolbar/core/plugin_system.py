#!/usr/bin/env python3
import os
import sys
import importlib.util
import inspect
import logging
import traceback
import json
from typing import Dict, List, Any, Optional, Type, Callable

logger = logging.getLogger(__name__)

class Plugin:
    """Base class for all plugins."""
    
    def initialize(self, config):
        """Initialize the plugin with the given configuration."""
        pass
    
    def cleanup(self):
        """Clean up resources used by the plugin."""
        pass
    
    def get_icon(self):
        """Get the icon for the plugin to display in the taskbar."""
        from PyQt5.QtGui import QIcon
        return QIcon.fromTheme("application-x-executable")
    
    def get_title(self):
        """Get the title for the plugin to display in the taskbar."""
        return self.name
    
    def activate(self):
        """Activate the plugin when its taskbar button is clicked."""
        pass
    
    @property
    def name(self):
        """Get the name of the plugin."""
        return self.__class__.__name__
    
    @property
    def version(self):
        """Get the version of the plugin."""
        return "1.0.0"
    
    @property
    def description(self):
        """Get the description of the plugin."""
        return "No description provided."
    
    @property
    def dependencies(self):
        """Get the list of plugin dependencies."""
        return []

class PluginManager:
    """Manages loading and accessing plugins."""
    
    def __init__(self, config):
        """Initialize the plugin manager with the given configuration."""
        self.config = config
        self.plugins = {}
        self.plugin_dirs = []
        self.failed_plugins = {}
        self.plugin_metadata = {}
        
        # Add default plugin directories
        self._add_default_plugin_dirs()
    
    def _add_default_plugin_dirs(self):
        """Add default plugin directories."""
        # Add the built-in plugins directory
        builtin_plugins_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")
        self.add_plugin_directory(builtin_plugins_dir)
        
        # Add user plugins directory from config
        user_plugins_dir = self.config.get_setting("plugins.user_dir")
        if user_plugins_dir and os.path.isdir(user_plugins_dir):
            self.add_plugin_directory(user_plugins_dir)
    
    def add_plugin_directory(self, directory):
        """Add a directory to search for plugins."""
        if os.path.isdir(directory) and directory not in self.plugin_dirs:
            self.plugin_dirs.append(directory)
            logger.info(f"Added plugin directory: {directory}")
    
    def load_plugins(self):
        """Load all plugins from the plugin directories."""
        # Clear existing plugins
        self.plugins = {}
        self.failed_plugins = {}
        self.plugin_metadata = {}
        
        # Get disabled plugins from config
        disabled_plugins = self.config.get_setting("plugins.disabled", [])
        
        # Discover all potential plugins first
        discovered_plugins = self._discover_plugins(disabled_plugins)
        
        # Sort plugins by dependencies
        sorted_plugins = self._sort_plugins_by_dependencies(discovered_plugins)
        
        # Load plugins in dependency order
        for plugin_info in sorted_plugins:
            try:
                self._load_plugin(plugin_info)
            except Exception as e:
                logger.error(f"Error loading plugin {plugin_info['name']}: {e}", exc_info=True)
                self.failed_plugins[plugin_info['name']] = str(e)
        
        logger.info(f"Loaded {len(self.plugins)} plugins")
        if self.failed_plugins:
            logger.warning(f"Failed to load {len(self.failed_plugins)} plugins")
    
    def _discover_plugins(self, disabled_plugins):
        """Discover all potential plugins in the plugin directories."""
        discovered_plugins = []
        
        for plugin_dir in self.plugin_dirs:
            if not os.path.isdir(plugin_dir):
                logger.warning(f"Plugin directory does not exist: {plugin_dir}")
                continue
            
            # Iterate through subdirectories
            for item in os.listdir(plugin_dir):
                item_path = os.path.join(plugin_dir, item)
                
                # Skip if not a directory or if it's a special directory
                if not os.path.isdir(item_path) or item.startswith("__"):
                    continue
                
                # Skip if plugin is disabled
                if item in disabled_plugins:
                    logger.info(f"Skipping disabled plugin: {item}")
                    continue
                
                # Check for plugin metadata
                metadata = self._get_plugin_metadata(item_path, item)
                if metadata:
                    discovered_plugins.append(metadata)
        
        return discovered_plugins
    
    def _get_plugin_metadata(self, plugin_dir, plugin_name):
        """Get metadata for a plugin."""
        # Check for metadata.json file
        metadata_path = os.path.join(plugin_dir, "metadata.json")
        metadata = {
            "name": plugin_name,
            "path": plugin_dir,
            "dependencies": [],
            "priority": 0
        }
        
        if os.path.isfile(metadata_path):
            try:
                with open(metadata_path, "r") as f:
                    file_metadata = json.load(f)
                    metadata.update(file_metadata)
            except Exception as e:
                logger.warning(f"Error loading metadata for plugin {plugin_name}: {e}")
        
        # Check for __init__.py
        init_path = os.path.join(plugin_dir, "__init__.py")
        if not os.path.isfile(init_path):
            logger.warning(f"Plugin {plugin_name} has no __init__.py file")
            return None
        
        return metadata
    
    def _sort_plugins_by_dependencies(self, plugins):
        """Sort plugins by dependencies to ensure proper loading order."""
        # Create a dependency graph
        graph = {}
        for plugin in plugins:
            graph[plugin["name"]] = plugin["dependencies"]
        
        # Perform topological sort
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(node):
            if node in temp_visited:
                # Circular dependency detected
                logger.warning(f"Circular dependency detected for plugin {node}")
                return
            
            if node not in visited:
                temp_visited.add(node)
                
                # Visit dependencies
                for dep in graph.get(node, []):
                    if dep in graph:  # Only visit if the dependency exists
                        visit(dep)
                
                temp_visited.remove(node)
                visited.add(node)
                order.append(node)
        
        # Visit all nodes
        for plugin in plugins:
            if plugin["name"] not in visited:
                visit(plugin["name"])
        
        # Reverse the order to get the correct loading sequence
        order.reverse()
        
        # Sort plugins by the order determined by topological sort
        # and then by priority for plugins with the same dependencies
        sorted_plugins = []
        for name in order:
            for plugin in plugins:
                if plugin["name"] == name:
                    sorted_plugins.append(plugin)
                    break
        
        # Sort plugins with the same dependencies by priority
        final_sorted = []
        current_group = []
        current_deps = None
        
        for plugin in sorted_plugins:
            if current_deps is None or set(plugin["dependencies"]) == set(current_deps):
                current_group.append(plugin)
                current_deps = plugin["dependencies"]
            else:
                # Sort the current group by priority
                current_group.sort(key=lambda p: p.get("priority", 0), reverse=True)
                final_sorted.extend(current_group)
                
                # Start a new group
                current_group = [plugin]
                current_deps = plugin["dependencies"]
        
        # Add the last group
        if current_group:
            current_group.sort(key=lambda p: p.get("priority", 0), reverse=True)
            final_sorted.extend(current_group)
        
        return final_sorted
    
    def _load_plugin(self, plugin_info):
        """Load a plugin based on its metadata."""
        plugin_dir = plugin_info["path"]
        plugin_name = plugin_info["name"]
        
        # Check for dependencies
        for dep in plugin_info.get("dependencies", []):
            if dep not in self.plugins:
                raise ImportError(f"Dependency {dep} not loaded")
        
        # Load the module
        init_path = os.path.join(plugin_dir, "__init__.py")
        try:
            spec = importlib.util.spec_from_file_location(f"toolkit.plugins.{plugin_name}", init_path)
            if spec is None:
                raise ImportError(f"Failed to create spec for {init_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin classes
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj is not Plugin):
                    plugin_classes.append(obj)
            
            if not plugin_classes:
                logger.warning(f"No plugin classes found in {plugin_name}")
                return
            
            # Initialize each plugin class
            for plugin_class in plugin_classes:
                plugin_instance = plugin_class()
                try:
                    plugin_instance.initialize(self.config)
                    self.plugins[plugin_instance.name] = plugin_instance
                    self.plugin_metadata[plugin_instance.name] = plugin_info
                    logger.info(f"Loaded plugin: {plugin_instance.name} v{plugin_instance.version}")
                except Exception as e:
                    logger.error(f"Error initializing plugin {plugin_instance.name}: {e}", exc_info=True)
                    self.failed_plugins[plugin_instance.name] = str(e)
        
        except Exception as e:
            logger.error(f"Error loading plugin module {plugin_name}: {e}", exc_info=True)
            self.failed_plugins[plugin_name] = str(e)
    
    def get_plugin(self, name):
        """Get a plugin by name."""
        return self.plugins.get(name)
    
    def get_all_plugins(self):
        """Get all loaded plugins."""
        return self.plugins
    
    def get_failed_plugins(self):
        """Get all plugins that failed to load."""
        return self.failed_plugins
    
    def get_plugin_metadata(self, name):
        """Get metadata for a plugin."""
        return self.plugin_metadata.get(name)
    
    def disable_plugin(self, name):
        """Disable a plugin."""
        # Get current disabled plugins
        disabled_plugins = self.config.get_setting("plugins.disabled", [])
        
        # Add the plugin to the disabled list if not already there
        if name not in disabled_plugins:
            disabled_plugins.append(name)
            self.config.set_setting("plugins.disabled", disabled_plugins)
            self.config.save()
            logger.info(f"Disabled plugin: {name}")
        
        # Remove the plugin from the loaded plugins if it's loaded
        if name in self.plugins:
            try:
                self.plugins[name].cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up plugin {name}: {e}", exc_info=True)
            
            del self.plugins[name]
    
    def enable_plugin(self, name):
        """Enable a previously disabled plugin."""
        # Get current disabled plugins
        disabled_plugins = self.config.get_setting("plugins.disabled", [])
        
        # Remove the plugin from the disabled list if it's there
        if name in disabled_plugins:
            disabled_plugins.remove(name)
            self.config.set_setting("plugins.disabled", disabled_plugins)
            self.config.save()
            logger.info(f"Enabled plugin: {name}")
        
        # The plugin will be loaded on the next load_plugins() call
    
    def cleanup(self):
        """Clean up all plugins."""
        for name, plugin in list(self.plugins.items()):
            try:
                plugin.cleanup()
                logger.info(f"Cleaned up plugin: {name}")
            except Exception as e:
                logger.error(f"Error cleaning up plugin {name}: {e}", exc_info=True)
        
        self.plugins = {}
