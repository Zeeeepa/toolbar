#!/usr/bin/env python3
import os
import sys
import logging
import importlib.util
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class EnhancedPluginManager:
    def __init__(self, config=None, event_bus=None, toolbar=None):
        self.config = config
        self.event_bus = event_bus
        self.toolbar = toolbar
        self.plugins = {}
        self.plugin_dirs = []
        self._load_plugin_directories()

    def _load_plugin_directories(self):
        """Load plugin directories from configuration"""
        try:
            # Add default plugin directory
            default_plugin_dir = os.path.join(os.path.dirname(__file__), "..", "plugins")
            self.add_plugin_directory(default_plugin_dir)

            # Add user plugin directory
            user_plugin_dir = os.path.expanduser("~/.toolbar/plugins")
            self.add_plugin_directory(user_plugin_dir)

            # Add configured plugin directories
            if self.config and "plugin_dirs" in self.config:
                for plugin_dir in self.config["plugin_dirs"]:
                    self.add_plugin_directory(plugin_dir)

        except Exception as e:
            logger.error(f"Error loading plugin directories: {str(e)}")
            logger.exception(e)

    def add_plugin_directory(self, directory: str):
        """Add a directory to search for plugins"""
        try:
            if os.path.exists(directory) and os.path.isdir(directory):
                if directory not in self.plugin_dirs:
                    self.plugin_dirs.append(directory)
                    logger.info(f"Added plugin directory: {directory}")
                    if self.config:
                        self.config.save()
        except Exception as e:
            logger.error(f"Error adding plugin directory {directory}: {str(e)}")
            logger.exception(e)

    def _load_enhanced_plugin(self, plugin_dir: str, plugin_name: str) -> Optional[object]:
        """Load a plugin from the given directory"""
        try:
            # Find plugin module
            plugin_path = os.path.join(plugin_dir, plugin_name)
            init_file = os.path.join(plugin_path, "__init__.py")
            
            if not os.path.exists(init_file):
                return None

            # Import plugin module
            spec = importlib.util.spec_from_file_location(
                f"Toolbar.plugins.{plugin_name}", init_file
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Get plugin class
            main_class_name = getattr(module, "MAIN_CLASS", None)
            if not main_class_name:
                main_class_name = "".join(word.capitalize() for word in plugin_name.split("_")) + "Plugin"

            main_class = getattr(module, main_class_name, None)
            if not main_class:
                raise ImportError(f"Main class not found: {main_class_name}")

            # Create plugin instance
            plugin_instance = main_class()
            plugin_instance.initialize(self.config, self.event_bus, self.toolbar)

            return plugin_instance

        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {str(e)}")
            logger.exception(e)
            return None

    def load_plugin(self, plugin_name: str) -> bool:
        """Load a specific plugin by name"""
        try:
            # Check if plugin is already loaded
            if plugin_name in self.plugins:
                return True

            # Try loading from plugin directories
            for plugin_dir in self.plugin_dirs:
                plugin = self._load_enhanced_plugin(plugin_dir, plugin_name)
                if plugin:
                    self.plugins[plugin_name] = plugin
                    logger.info(f"Loaded plugin: {plugin_name} v{plugin.version}")
                    return True

            logger.warning(f"Plugin not found: {plugin_name}")
            return False

        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {str(e)}")
            logger.exception(e)
            return False

    def get_all_plugins(self) -> List[object]:
        """Get all loaded plugins"""
        return list(self.plugins.values())

    def get_plugin(self, plugin_name: str) -> Optional[object]:
        """Get a specific plugin by name"""
        return self.plugins.get(plugin_name)

    def activate_plugin(self, plugin_name: str) -> bool:
        """Activate a plugin"""
        try:
            plugin = self.get_plugin(plugin_name)
            if plugin and hasattr(plugin, "activate"):
                plugin.activate()
                logger.info(f"Activated plugin: {plugin_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error activating plugin {plugin_name}: {str(e)}")
            logger.exception(e)
            return False

    def deactivate_plugin(self, plugin_name: str) -> bool:
        """Deactivate a plugin"""
        try:
            plugin = self.get_plugin(plugin_name)
            if plugin and hasattr(plugin, "deactivate"):
                plugin.deactivate()
                logger.info(f"Deactivated plugin: {plugin_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deactivating plugin {plugin_name}: {str(e)}")
            logger.exception(e)
            return False

    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin"""
        try:
            if plugin_name in self.plugins:
                self.deactivate_plugin(plugin_name)
                del self.plugins[plugin_name]
            return self.load_plugin(plugin_name)
        except Exception as e:
            logger.error(f"Error reloading plugin {plugin_name}: {str(e)}")
            logger.exception(e)
            return False

    def load_all_plugins(self):
        """Load all plugins from plugin directories"""
        try:
            for plugin_dir in self.plugin_dirs:
                if not os.path.exists(plugin_dir):
                    continue
                    
                for item in os.listdir(plugin_dir):
                    if os.path.isdir(os.path.join(plugin_dir, item)):
                        self.load_plugin(item)
        except Exception as e:
            logger.error(f"Error loading all plugins: {str(e)}")
            logger.exception(e)
