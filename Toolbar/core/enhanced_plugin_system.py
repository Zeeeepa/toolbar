#!/usr/bin/env python3
import os
import logging
import importlib.util
from typing import Dict, List, Optional, Any, Type

from .plugin_system import Plugin, PluginManifest, BasePluginManager
from PyQt5.QtGui import QIcon

logger = logging.getLogger(__name__)

class EnhancedPluginManifest(PluginManifest):
    """Enhanced plugin manifest with additional metadata."""
    
    def __init__(self, name: str, version: str, description: str = "", icon_path: str = ""):
        super().__init__(name, version, description)
        self.icon_path = icon_path

class EnhancedPlugin(Plugin):
    """Enhanced plugin base class with additional functionality."""
    
    def __init__(self):
        super().__init__()
        self._manifest = None
        self._icon = None
        
    @property
    def name(self) -> str:
        """Get plugin name."""
        return self._manifest.name if self._manifest else "Unknown Plugin"
        
    @property
    def version(self) -> str:
        """Get plugin version."""
        return self._manifest.version if self._manifest else "0.0.0"
        
    @property
    def description(self) -> str:
        """Get plugin description."""
        return self._manifest.description if self._manifest else ""
        
    def get_icon(self) -> Optional[QIcon]:
        """Get plugin icon."""
        if self._icon is None and self._manifest and self._manifest.icon_path:
            try:
                # Try to load icon from manifest path
                icon_path = os.path.join(os.path.dirname(self.__module__), self._manifest.icon_path)
                if os.path.exists(icon_path):
                    self._icon = QIcon(icon_path)
                else:
                    # Try to load from resources
                    self._icon = QIcon(f":/icons/{self._manifest.icon_path}")
            except Exception as e:
                logger.warning(f"Failed to load icon for plugin {self.name}: {e}")
                self._icon = QIcon()  # Empty icon
                
        return self._icon
        
    def activate(self) -> None:
        """Activate the plugin."""
        try:
            self.on_activate()
        except Exception as e:
            logger.error(f"Error activating plugin {self.name}: {e}")
            raise
            
    def deactivate(self) -> None:
        """Deactivate the plugin."""
        try:
            self.on_deactivate()
        except Exception as e:
            logger.error(f"Error deactivating plugin {self.name}: {e}")
            raise
            
    def on_activate(self) -> None:
        """Called when plugin is activated."""
        pass
        
    def on_deactivate(self) -> None:
        """Called when plugin is deactivated."""
        pass

class EnhancedPluginManager(BasePluginManager):
    """Enhanced plugin manager with improved loading and error handling."""
    
    def __init__(self):
        super().__init__()
        self._plugins: Dict[str, EnhancedPlugin] = {}
        
    def load_plugin(self, plugin_path: str) -> Optional[EnhancedPlugin]:
        """Load a plugin from the given path."""
        try:
            return self._load_enhanced_plugin(plugin_path)
        except Exception as e:
            logger.error(f"Error loading plugin from {plugin_path}: {e}")
            return None
            
    def _load_enhanced_plugin(self, plugin_path: str) -> Optional[EnhancedPlugin]:
        """Internal method to load an enhanced plugin."""
        try:
            # Import the plugin module
            module_name = os.path.basename(plugin_path).replace(".py", "")
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if not spec or not spec.loader:
                raise ImportError(f"Could not load spec for {plugin_path}")
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the plugin class
            plugin_class = None
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (isinstance(item, type) and 
                    issubclass(item, EnhancedPlugin) and 
                    item != EnhancedPlugin):
                    plugin_class = item
                    break
                    
            if not plugin_class:
                raise ImportError(f"No plugin class found in {plugin_path}")
                
            # Create plugin instance
            plugin = plugin_class()
            
            # Load manifest if available
            manifest_path = os.path.join(os.path.dirname(plugin_path), "manifest.json")
            if os.path.exists(manifest_path):
                import json
                with open(manifest_path) as f:
                    manifest_data = json.load(f)
                    plugin._manifest = EnhancedPluginManifest(**manifest_data)
                    
            return plugin
            
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_path}: {e}")
            raise
            
    def get_plugins(self) -> List[EnhancedPlugin]:
        """Get all loaded plugins."""
        return list(self._plugins.values())
        
    def get_plugin(self, plugin_id: str) -> Optional[EnhancedPlugin]:
        """Get a specific plugin by ID."""
        return self._plugins.get(plugin_id)
        
    def register_plugin(self, plugin_id: str, plugin: EnhancedPlugin) -> None:
        """Register a plugin with the manager."""
        if plugin_id in self._plugins:
            logger.warning(f"Plugin {plugin_id} already registered, replacing")
        self._plugins[plugin_id] = plugin
        
    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister a plugin."""
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
