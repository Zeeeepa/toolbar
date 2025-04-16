#!/usr/bin/env python3
import os
import sys
import logging
import importlib
import importlib.util
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class EnhancedPlugin:
    """Base class for enhanced plugins"""
    def __init__(self):
        self.name = "Base Plugin"
        self.version = "1.0.0"
        self.description = "Base plugin class"
        self._active = False

    def initialize(self, config=None, event_bus=None, toolbar=None):
        """Initialize the plugin"""
        pass

    def activate(self):
        """Activate the plugin"""
        self._active = True

    def deactivate(self):
        """Deactivate the plugin"""
        self._active = False

    def is_active(self) -> bool:
        """Check if plugin is active"""
        return self._active

    def get_icon(self) -> str:
        """Get plugin icon path"""
        return ""

    def get_actions(self) -> List[Dict[str, Any]]:
        """Get plugin actions"""
        return []

    def handle_click(self):
        """Handle plugin button click"""
        pass

class EnhancedPluginManager:
    """Enhanced plugin manager with improved error handling"""
    def __init__(self, config=None):
        self.config = config
        self.plugins: Dict[str, EnhancedPlugin] = {}
        self.plugin_dirs = []
        self._load_plugin_directories()

    def _load_plugin_directories(self):
        """Load plugin directories from config"""
        try:
            # Add default plugin directory
            default_dir = os.path.join(os.path.dirname(__file__), "..", "plugins")
            self.add_plugin_directory(default_dir)

            # Add user plugin directory
            user_dir = os.path.expanduser("~/.toolbar/plugins")
            self.add_plugin_directory(user_dir)

            # Add configured plugin directories
            if self.config and hasattr(self.config, "get"):
                plugin_dirs = self.config.get("plugin_dirs", [])
                for directory in plugin_dirs:
                    self.add_plugin_directory(directory)

        except Exception as e:
            logger.error(f"Error loading plugin directories: {str(e)}")
            logger.error(str(e), exc_info=True)

    def add_plugin_directory(self, directory: str):
        """Add a plugin directory"""
        if os.path.exists(directory) and directory not in self.plugin_dirs:
            self.plugin_dirs.append(directory)
            logger.info(f"Added plugin directory: {directory}")

    def _load_enhanced_plugin(self, plugin_dir: str, plugin_name: str) -> Optional[EnhancedPlugin]:
        """Load a plugin from directory"""
        try:
            # Import plugin module
            module_path = os.path.join(plugin_dir, plugin_name)
            if not os.path.isdir(module_path):
                return None

            init_path = os.path.join(module_path, "__init__.py")
            if not os.path.exists(init_path):
                return None

            module_name = f"Toolbar.plugins.{plugin_name}"
            spec = importlib.util.spec_from_file_location(module_name, init_path)
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Get plugin class
            main_class_name = f"{plugin_name.title()}Plugin"
            if not hasattr(module, main_class_name):
                raise ImportError(f"Main class not found: {main_class_name}")

            # Create plugin instance
            plugin_class = getattr(module, main_class_name)
            plugin_instance = plugin_class()

            # Initialize plugin
            plugin_instance.initialize(self.config)
            return plugin_instance

        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {str(e)}")
            logger.error(str(e), exc_info=True)
            return None

    def load_plugins(self):
        """Load all plugins from plugin directories"""
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                continue

            for item in os.listdir(plugin_dir):
                if item.startswith("__"):
                    continue

                plugin = self._load_enhanced_plugin(plugin_dir, item)
                if plugin:
                    self.plugins[item] = plugin
                    logger.info(f"Loaded plugin: {plugin.name} v{plugin.version}")
                else:
                    logger.warning(f"Plugin not found: {item}")

    def reload_plugins(self):
        """Reload all plugins"""
        self.plugins.clear()
        self.load_plugins()

    def get_plugin(self, name: str) -> Optional[EnhancedPlugin]:
        """Get a plugin by name"""
        return self.plugins.get(name)

    def get_all_plugins(self) -> List[EnhancedPlugin]:
        """Get all loaded plugins"""
        return list(self.plugins.values())

    def get_active_plugins(self) -> List[EnhancedPlugin]:
        """Get all active plugins"""
        return [p for p in self.plugins.values() if p.is_active()]
