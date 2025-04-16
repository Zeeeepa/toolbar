#!/usr/bin/env python3
import os
import sys
import importlib.util
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class EnhancedPlugin:
    """Base class for all enhanced plugins."""
    
    def __init__(self):
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
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def description(self) -> str:
        return self._description

    @property
    def icon(self) -> Optional[str]:
        return self._icon

    def is_active(self) -> bool:
        return self._active

    def initialize(self, config: Any, event_bus: Any, toolbar: Any) -> None:
        """Initialize the plugin with configuration and dependencies."""
        self._config = config
        self._event_bus = event_bus
        self._toolbar = toolbar
        self._active = True

    def cleanup(self) -> None:
        """Clean up any resources used by the plugin."""
        self._active = False

class EnhancedPluginManager:
    """Manager for loading and handling enhanced plugins."""
    
    def __init__(self, config: Any):
        self.config = config
        self.plugins: Dict[str, EnhancedPlugin] = {}
        self.plugin_dirs: List[str] = []
        self._load_plugin_directories()

    def _load_plugin_directories(self) -> None:
        """Load plugin directories from configuration."""
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            plugins_dir = os.path.join(base_dir, "plugins")
            self.add_plugin_directory(plugins_dir)

            user_plugins_dir = os.path.expanduser("~/.toolbar/plugins")
            self.add_plugin_directory(user_plugins_dir)
        except Exception as e:
            logger.error(f"Error loading plugin directories: {str(e)}")
            logger.error(str(e), exc_info=True)

    def add_plugin_directory(self, directory: str) -> None:
        """Add a directory to search for plugins."""
        if os.path.exists(directory) and directory not in self.plugin_dirs:
            self.plugin_dirs.append(directory)
            logger.info(f"Added plugin directory: {directory}")

    def load_plugin(self, plugin_name: str) -> Optional[EnhancedPlugin]:
        """Load a plugin by name."""
        try:
            for plugin_dir in self.plugin_dirs:
                plugin_path = os.path.join(plugin_dir, plugin_name)
                if os.path.exists(plugin_path):
                    return self._load_enhanced_plugin(plugin_path, plugin_name)
            logger.warning(f"Plugin not found: {plugin_name}")
            return None
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {str(e)}")
            logger.error(str(e), exc_info=True)
            return None

    def _load_enhanced_plugin(self, plugin_path: str, plugin_name: str) -> Optional[EnhancedPlugin]:
        """Load an enhanced plugin from a directory."""
        try:
            sys.path.insert(0, os.path.dirname(plugin_path))
            module_name = os.path.basename(plugin_path)
            spec = importlib.util.spec_from_file_location(module_name, os.path.join(plugin_path, "__init__.py"))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                main_class_name = f"{module_name.capitalize()}Plugin"
                if hasattr(module, main_class_name):
                    plugin_class = getattr(module, main_class_name)
                    plugin_instance = plugin_class()
                    self.plugins[plugin_name] = plugin_instance
                    return plugin_instance
                raise ImportError(f"Main class not found: {main_class_name}")
            return None
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {str(e)}")
            logger.error(str(e), exc_info=True)
            return None
        finally:
            if os.path.dirname(plugin_path) in sys.path:
                sys.path.remove(os.path.dirname(plugin_path))

    def get_plugin(self, plugin_name: str) -> Optional[EnhancedPlugin]:
        """Get a loaded plugin by name."""
        return self.plugins.get(plugin_name)

    def get_all_plugins(self) -> List[EnhancedPlugin]:
        """Get all loaded plugins."""
        return list(self.plugins.values())

    def initialize_plugin(self, plugin_name: str, config: Any, event_bus: Any, toolbar: Any) -> bool:
        """Initialize a plugin with configuration and dependencies."""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            try:
                plugin.initialize(config, event_bus, toolbar)
                return True
            except Exception as e:
                logger.error(f"Error initializing plugin {plugin_name}: {str(e)}")
                logger.error(str(e), exc_info=True)
        return False

    def cleanup_plugin(self, plugin_name: str) -> bool:
        """Clean up a plugin's resources."""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            try:
                plugin.cleanup()
                return True
            except Exception as e:
                logger.error(f"Error cleaning up plugin {plugin_name}: {str(e)}")
                logger.error(str(e), exc_info=True)
        return False
