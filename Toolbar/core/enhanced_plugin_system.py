#!/usr/bin/env python3
import os
import importlib.util
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class EnhancedPlugin:
    """Base class for all enhanced plugins"""
    def __init__(self):
        self.name = ""
        self.version = "1.0.0"
        self.description = ""
        self.icon = None
        self.active = False
        self.config = None
        self.event_bus = None
        self.toolbar = None

    def initialize(self, config: Any, event_bus: Any, toolbar: Any) -> None:
        """Initialize the plugin with configuration"""
        self.config = config
        self.event_bus = event_bus
        self.toolbar = toolbar
        self.active = True

    def get_icon(self) -> str:
        """Get the plugin's icon path"""
        return self.icon or ""

    def get_actions(self) -> List[Dict[str, Any]]:
        """Get the plugin's available actions"""
        return []

    def is_active(self) -> bool:
        """Check if the plugin is active"""
        return self.active

class EnhancedPluginManager:
    """Manager for enhanced plugins"""
    def __init__(self, config: Any):
        self.config = config
        self.plugins: Dict[str, EnhancedPlugin] = {}
        self.plugin_dirs: List[str] = []
        self._load_plugin_directories()

    def _load_plugin_directories(self) -> None:
        """Load plugin directories from configuration"""
        try:
            # Add default plugin directories
            base_dir = os.path.dirname(os.path.dirname(__file__))
            plugins_dir = os.path.join(base_dir, "plugins")
            self.add_plugin_directory(plugins_dir)

            # Add user plugin directory
            user_plugins_dir = os.path.expanduser("~/.toolbar/plugins")
            self.add_plugin_directory(user_plugins_dir)

            # Add configured plugin directories
            if hasattr(self.config, "plugin_dirs"):
                for plugin_dir in self.config.plugin_dirs:
                    self.add_plugin_directory(plugin_dir)
        except Exception as e:
            logger.error("Error loading plugin directories: %s", str(e))
            logger.error(str(e), exc_info=True)

    def add_plugin_directory(self, directory: str) -> None:
        """Add a directory to search for plugins"""
        if directory not in self.plugin_dirs:
            self.plugin_dirs.append(directory)
            logger.info("Added plugin directory: %s", directory)

    def _load_enhanced_plugin(self, plugin_dir: str, plugin_name: str) -> Optional[EnhancedPlugin]:
        """Load a plugin from a directory"""
        try:
            # Import the plugin module
            plugin_path = os.path.join(plugin_dir, plugin_name)
            init_path = os.path.join(plugin_path, "__init__.py")
            
            if not os.path.exists(init_path):
                return None

            spec = importlib.util.spec_from_file_location(
                f"Toolbar.plugins.{plugin_name}", init_path
            )
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the plugin class
            main_class_name = f"{plugin_name.title()}Plugin"
            if not hasattr(module, main_class_name):
                raise ImportError(f"Main class not found: {main_class_name}")

            plugin_class = getattr(module, main_class_name)
            plugin_instance = plugin_class()
            return plugin_instance

        except Exception as e:
            logger.error("Error loading plugin %s: %s", plugin_name, str(e))
            logger.error(str(e), exc_info=True)
            return None

    def load_plugins(self) -> None:
        """Load all plugins from configured directories"""
        for plugin_dir in self.plugin_dirs:
            if not os.path.exists(plugin_dir):
                continue

            for item in os.listdir(plugin_dir):
                if os.path.isdir(os.path.join(plugin_dir, item)) and not item.startswith("__"):
                    plugin = self._load_enhanced_plugin(plugin_dir, item)
                    if plugin:
                        self.plugins[item] = plugin

    def get_plugin(self, name: str) -> Optional[EnhancedPlugin]:
        """Get a plugin by name"""
        return self.plugins.get(name)

    def get_all_plugins(self) -> List[EnhancedPlugin]:
        """Get all loaded plugins"""
        return list(self.plugins.values())

    def get_active_plugins(self) -> List[EnhancedPlugin]:
        """Get all active plugins"""
        return [p for p in self.plugins.values() if p.is_active()]
