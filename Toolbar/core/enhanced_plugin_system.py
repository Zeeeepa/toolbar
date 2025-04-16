#!/usr/bin/env python3
import os
import sys
import importlib.util
import inspect
import logging
import json
import traceback
import threading
import time
import pkgutil
import zipfile
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Type, Callable, Set, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field, asdict
from PyQt5.QtCore import QObject, pyqtSignal, QSettings, QDir

# Import the original plugin system to extend it
from Toolbar.core.plugin_system import (
    Plugin, PluginState, PluginType, PluginEvent, EventBus, 
    PluginDependency, PluginManifest, PluginManager as BasePluginManager,
    GitHubPlugin, LinearPlugin, AutomationPlugin
)

logger = logging.getLogger(__name__)

# Define new plugin types
class ExtendedPluginType(Enum):
    """Extended enum representing additional types of plugins."""
    CORE = "core"
    UI = "ui"
    INTEGRATION = "integration"
    AUTOMATION = "automation"
    UTILITY = "utility"
    PROMPT = "prompt"
    AI = "ai"
    SCRIPTING = "scripting"
    THEME = "theme"
    EXTENSION = "extension"
    OTHER = "other"

@dataclass
class PluginLocation:
    """Class representing a plugin location configuration."""
    id: str
    name: str
    path: str
    enabled: bool = True
    auto_discover: bool = True
    priority: int = 100
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginLocation':
        """Create a PluginLocation from a dictionary."""
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            path=data.get("path"),
            enabled=data.get("enabled", True),
            auto_discover=data.get("auto_discover", True),
            priority=data.get("priority", 100)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

@dataclass
class EnhancedPluginManifest(PluginManifest):
    """Enhanced class representing a plugin manifest with additional fields."""
    # Required parameters must come first (inherited from PluginManifest)
    id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: Union[PluginType, ExtendedPluginType]
    main_class: str
    # Optional parameters with default values
    dependencies: List[PluginDependency] = None
    min_toolbar_version: str = "1.0.0"
    max_toolbar_version: str = "*"
    settings_schema: Dict[str, Any] = None
    # Additional fields specific to EnhancedPluginManifest
    icon_path: Optional[str] = None
    settings_ui_class: Optional[str] = None
    website: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    auto_start: bool = False
    update_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedPluginManifest':
        """Create an EnhancedPluginManifest from a dictionary."""
        # Convert plugin_type string to enum
        plugin_type_str = data.get("plugin_type", "other")
        try:
            plugin_type = ExtendedPluginType(plugin_type_str)
        except ValueError:
            try:
                plugin_type = PluginType(plugin_type_str)
            except ValueError:
                plugin_type = PluginType.OTHER
        
        # Convert dependencies list
        dependencies = []
        for dep in data.get("dependencies", []):
            dependencies.append(PluginDependency(
                plugin_id=dep.get("plugin_id"),
                version_requirement=dep.get("version_requirement", "*"),
                optional=dep.get("optional", False)
            ))
        
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            version=data.get("version"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            plugin_type=plugin_type,
            main_class=data.get("main_class"),
            dependencies=dependencies,
            min_toolbar_version=data.get("min_toolbar_version", "1.0.0"),
            max_toolbar_version=data.get("max_toolbar_version", "*"),
            settings_schema=data.get("settings_schema"),
            icon_path=data.get("icon_path"),
            settings_ui_class=data.get("settings_ui_class"),
            website=data.get("website"),
            repository=data.get("repository"),
            license=data.get("license"),
            tags=data.get("tags", []),
            required_permissions=data.get("required_permissions", []),
            auto_start=data.get("auto_start", False),
            update_url=data.get("update_url")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert enums to strings
        data["plugin_type"] = self.plugin_type.value if self.plugin_type else "other"
        # Convert dependencies to dicts
        if self.dependencies:
            data["dependencies"] = [asdict(dep) for dep in self.dependencies]
        return data

class EnhancedPlugin(Plugin):
    """Enhanced base class for all plugins with additional functionality."""
    
    def __init__(self):
        """Initialize the plugin."""
        super().__init__()
        self._settings = None
        self._location = None
        self._auto_start = False
        self._permissions = set()
    
    def initialize(self, config, event_bus=None, toolbar=None):
        """Initialize the plugin with the given configuration and event bus."""
        result = super().initialize(config, event_bus, toolbar)
        
        # Initialize plugin settings
        if config and self.id:
            self._settings = QSettings(self.id, "Toolbar")
            
            # Set auto-start from manifest
            if self._manifest and hasattr(self._manifest, "auto_start"):
                self._auto_start = self._manifest.auto_start
        
        return result
    
    def auto_start(self) -> bool:
        """Check if the plugin should auto-start."""
        return self._auto_start
    
    def set_location(self, location: PluginLocation):
        """Set the plugin location."""
        self._location = location
    
    def get_location(self) -> Optional[PluginLocation]:
        """Get the plugin location."""
        return self._location
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a plugin-specific setting."""
        # First try the enhanced settings
        if self._settings:
            value = self._settings.value(key, None)
            if value is not None:
                return value
        
        # Fall back to the original implementation
        return super().get_setting(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a plugin-specific setting."""
        # Use the enhanced settings
        if self._settings:
            self._settings.setValue(key, value)
            self._settings.sync()
        
        # Also use the original implementation for compatibility
        super().set_setting(key, value)
    
    def has_permission(self, permission: str) -> bool:
        """Check if the plugin has a specific permission."""
        return permission in self._permissions
    
    def request_permission(self, permission: str) -> bool:
        """Request a permission for the plugin."""
        # This would typically show a dialog to the user
        # For now, just add the permission
        self._permissions.add(permission)
        return True
    
    def get_icon(self):
        """Get the icon for the plugin to display in the taskbar."""
        from PyQt5.QtGui import QIcon
        
        # Check if the manifest has an icon path
        if self._manifest and hasattr(self._manifest, "icon_path") and self._manifest.icon_path:
            icon_path = self._manifest.icon_path
            
            # If the path is relative, make it absolute
            if not os.path.isabs(icon_path) and self._location and self._location.path:
                icon_path = os.path.join(self._location.path, icon_path)
            
            # Check if the file exists
            if os.path.isfile(icon_path):
                return QIcon(icon_path)
        
        # Fall back to the original implementation
        return super().get_icon()

class PromptPlugin(EnhancedPlugin):
    """Interface for prompt template plugins."""
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """Get the list of prompt templates."""
        return []
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific prompt template."""
        return None
    
    def render_template(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Render a prompt template with variables."""
        return ""
    
    def create_template(self, template: Dict[str, Any]) -> bool:
        """Create a new prompt template."""
        return False
    
    def update_template(self, template_id: str, template: Dict[str, Any]) -> bool:
        """Update an existing prompt template."""
        return False
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a prompt template."""
        return False

class ScriptingPlugin(EnhancedPlugin):
    """Interface for scripting plugins."""
    
    def get_scripts(self) -> List[Dict[str, Any]]:
        """Get the list of scripts."""
        return []
    
    def get_script(self, script_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific script."""
        return None
    
    def run_script(self, script_id: str, params: Dict[str, Any] = None) -> Any:
        """Run a script with parameters."""
        return None
    
    def create_script(self, script: Dict[str, Any]) -> bool:
        """Create a new script."""
        return False
    
    def update_script(self, script_id: str, script: Dict[str, Any]) -> bool:
        """Update an existing script."""
        return False
    
    def delete_script(self, script_id: str) -> bool:
        """Delete a script."""
        return False

class EnhancedPluginManager(QObject):
    """Enhanced plugin manager with proper initialization and lifecycle management."""
    
    plugin_loaded = pyqtSignal(str)
    plugin_activated = pyqtSignal(str)
    plugin_deactivated = pyqtSignal(str)

    def __init__(self, config=None, event_bus=None, toolbar=None):
        super().__init__()
        self.config = config
        self.event_bus = event_bus
        self.toolbar = toolbar
        self._plugins: Dict[str, object] = {}
        self._active_plugins: Dict[str, object] = {}

    def load_plugin(self, plugin_dir: str, plugin_name: str) -> Optional[object]:
        """Load a plugin from the given directory."""
        try:
            # Import the plugin module
            module_path = f"Toolbar.plugins.{plugin_name}"
            module = importlib.import_module(module_path)

            # Get the main plugin class
            main_class_name = self._get_main_class_name(plugin_dir)
            if not main_class_name:
                raise ImportError(f"Main class not found in {plugin_name}")

            # Initialize plugin
            main_class = getattr(module, main_class_name)
            plugin_instance = main_class()
            
            # Initialize with dependencies
            plugin_instance.initialize(self.config, self.event_bus, self.toolbar)
            
            # Store plugin
            self._plugins[plugin_name] = plugin_instance
            logger.info(f"Loaded plugin: {plugin_name} v{plugin_instance.version}")
            
            return plugin_instance

        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {str(e)}")
            return None

    def activate_plugin(self, plugin_name: str) -> bool:
        """Activate a loaded plugin."""
        if plugin_name not in self._plugins:
            return False
            
        try:
            plugin = self._plugins[plugin_name]
            plugin.on_activate()
            self._active_plugins[plugin_name] = plugin
            self.plugin_activated.emit(plugin_name)
            logger.info(f"Activated plugin: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"Error activating plugin {plugin_name}: {str(e)}")
            return False

    def deactivate_plugin(self, plugin_name: str) -> bool:
        """Deactivate an active plugin."""
        if plugin_name not in self._active_plugins:
            return False
            
        try:
            plugin = self._active_plugins[plugin_name]
            plugin.on_deactivate()
            del self._active_plugins[plugin_name]
            self.plugin_deactivated.emit(plugin_name)
            logger.info(f"Deactivated plugin: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"Error deactivating plugin {plugin_name}: {str(e)}")
            return False

    def get_active_plugins(self) -> List[object]:
        """Get list of currently active plugins."""
        return list(self._active_plugins.values())

    def get_all_plugins(self) -> List[object]:
        """Get list of all loaded plugins."""
        return list(self._plugins.values())

    def _get_main_class_name(self, plugin_dir: str) -> Optional[str]:
        """Get the main plugin class name from manifest."""
        manifest_path = os.path.join(plugin_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            return None
            
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
                return manifest.get("main_class")
        except Exception:
            return None
