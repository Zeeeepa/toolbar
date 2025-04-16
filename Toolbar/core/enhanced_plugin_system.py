#!/usr/bin/env python3
import os
import sys
import importlib.util
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

class EnhancedPlugin:
    """Base class for enhanced plugins."""
    
    def __init__(self) -> None:
        self._name = ""
        self._version = "1.0.0"
        self._description = ""
        self._icon = None
        self._active = False
        self._config = None
        self._event_bus = None
        self._toolbar = None

    @property
    def name(self) -> str:
        """Get the plugin name."""
        return self._name

    @property
    def version(self) -> str:
        """Get the plugin version."""
        return self._version

    @property
    def description(self) -> str:
        """Get the plugin description."""
        return self._description

    @property
    def icon(self) -> Optional[str]:
        """Get the plugin icon path."""
        return self._icon

    @property
    def is_active(self) -> bool:
        """Check if the plugin is active."""
        return self._active

    def initialize(self, config: Any, event_bus: Any, toolbar: Any) -> None:
        """Initialize the plugin with configuration and dependencies."""
        self._config = config
        self._event_bus = event_bus
        self._toolbar = toolbar
        self._active = True

    def get_actions(self) -> List[Dict[str, Any]]:
        """Get the list of actions supported by this plugin."""
        return []

    def execute_action(self, action_id: str, params: Dict[str, Any]) -> Any:
        """Execute a plugin action."""
        raise NotImplementedError(f"Action {action_id} not implemented")

class EnhancedPluginManager:
    """Manager for enhanced plugins."""
    
    def __init__(self, config: Any = None) -> None:
        self._plugins: Dict[str, EnhancedPlugin] = {}
        self._config = config
        self._event_bus = None
        self._toolbar = None
        self._plugin_dirs = []
        self._load_plugin_directories()

    def _load_plugin_directories(self) -> None:
        """Load plugin directories from configuration."""
        try:
            # Add default plugin directories
            script_dir = os.path.dirname(os.path.abspath(__file__))
            default_plugin_dir = os.path.join(script_dir, "..", "plugins")
            self.add_plugin_directory(default_plugin_dir)

            # Add user plugin directory
            user_plugin_dir = os.path.expanduser("~/.toolbar/plugins")
            self.add_plugin_directory(user_plugin_dir)

            # Add configured plugin directories
            if self._config and hasattr(self._config, "plugin_dirs"):
                for plugin_dir in self._config.plugin_dirs:
                    self.add_plugin_directory(plugin_dir)
        except Exception as e:
            logger.error("Error loading plugin directories: %s", str(e))
            logger.error(str(e), exc_info=True)

    def add_plugin_directory(self, directory: str) -> None:
        """Add a directory to search for plugins."""
        directory = os.path.abspath(directory)
        if directory not in self._plugin_dirs:
            self._plugin_dirs.append(directory)
            logger.info("Added plugin directory: %s", directory)
            if self._config:
                self._config.save()

    def load_all_plugins(self) -> None:
        """Load all plugins from configured directories."""
        for plugin_dir in self._plugin_dirs:
            if os.path.exists(plugin_dir):
                for item in os.listdir(plugin_dir):
                    item_path = os.path.join(plugin_dir, item)
                    if os.path.isdir(item_path):
                        try:
                            self._load_enhanced_plugin(item, item_path)
                        except Exception as e:
                            logger.error("Error loading plugin %s: %s", item, str(e))
                            logger.error(str(e), exc_info=True)
                            logger.warning("Plugin not found: %s", item)

    def _load_enhanced_plugin(self, plugin_name: str, plugin_path: str) -> None:
        """Load a plugin from the specified path."""
        try:
            # Import the plugin module
            module_path = os.path.join(plugin_path, "__init__.py")
            if not os.path.exists(module_path):
                raise ImportError(f"Plugin {plugin_name} has no __init__.py")

            spec = importlib.util.spec_from_file_location(plugin_name, module_path)
            if not spec or not spec.loader:
                raise ImportError(f"Failed to load plugin {plugin_name}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = module
            spec.loader.exec_module(module)

            # Find the plugin class
            main_class_name = f"{plugin_name.capitalize()}Plugin"
            if not hasattr(module, main_class_name):
                raise ImportError(f"Main class not found: {main_class_name}")

            # Create plugin instance
            plugin_class = getattr(module, main_class_name)
            plugin_instance = plugin_class()

            # Initialize the plugin
            plugin_instance.initialize(self._config, self._event_bus, self._toolbar)

            # Store the plugin
            self._plugins[plugin_name] = plugin_instance
            logger.info("Loaded plugin: %s v%s", plugin_instance.name, plugin_instance.version)

        except Exception as e:
            logger.error("Error loading plugin %s: %s", plugin_name, str(e))
            logger.error(str(e), exc_info=True)
            raise

    def get_plugin(self, name: str) -> Optional[EnhancedPlugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def get_all_plugins(self) -> List[EnhancedPlugin]:
        """Get all loaded plugins."""
        return list(self._plugins.values())

    def get_active_plugins(self) -> List[EnhancedPlugin]:
        """Get all active plugins."""
        return [p for p in self._plugins.values() if p.is_active]

    def set_event_bus(self, event_bus: Any) -> None:
        """Set the event bus for plugins."""
        self._event_bus = event_bus

    def set_toolbar(self, toolbar: Any) -> None:
        """Set the toolbar instance for plugins."""
        self._toolbar = toolbar
