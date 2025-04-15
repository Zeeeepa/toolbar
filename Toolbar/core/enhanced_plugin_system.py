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
    # Add new fields
    plugin_type: Union[PluginType, ExtendedPluginType] = PluginType.OTHER
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

class EnhancedPluginManager(BasePluginManager):
    """Enhanced plugin manager with additional functionality."""
    
    def __init__(self, config):
        """Initialize the plugin manager."""
        super().__init__(config)
        self.plugin_locations = []
        self.plugin_zip_cache = {}
        self.plugin_update_checker = None
        self.auto_discovery_enabled = True
        
        # Load plugin locations from config
        self._load_plugin_locations()
        
        # Start plugin update checker
        self._start_update_checker()
    
    def _load_plugin_locations(self):
        """Load plugin locations from configuration."""
        locations = self.config.get_setting("plugins.locations", [])
        
        # Convert to PluginLocation objects
        for location_data in locations:
            try:
                location = PluginLocation.from_dict(location_data)
                self.add_plugin_location(location)
            except Exception as e:
                logger.error(f"Error loading plugin location: {e}", exc_info=True)
        
        # Add default locations if none are configured
        if not self.plugin_locations:
            # Add the built-in plugins directory
            builtin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
            self.add_plugin_location(PluginLocation(
                id="builtin",
                name="Built-in Plugins",
                path=builtin_dir,
                enabled=True,
                auto_discover=True,
                priority=100
            ))
            
            # Add user plugins directory
            user_dir = os.path.expanduser("~/.toolbar/plugins")
            os.makedirs(user_dir, exist_ok=True)
            self.add_plugin_location(PluginLocation(
                id="user",
                name="User Plugins",
                path=user_dir,
                enabled=True,
                auto_discover=True,
                priority=200
            ))
    
    def _save_plugin_locations(self):
        """Save plugin locations to configuration."""
        locations = [location.to_dict() for location in self.plugin_locations]
        self.config.set_setting("plugins.locations", locations)
        self.config.save()
    
    def add_plugin_location(self, location: PluginLocation):
        """Add a plugin location."""
        # Check if the location already exists
        for existing in self.plugin_locations:
            if existing.id == location.id:
                # Update the existing location
                existing.name = location.name
                existing.path = location.path
                existing.enabled = location.enabled
                existing.auto_discover = location.auto_discover
                existing.priority = location.priority
                return
        
        # Add the new location
        self.plugin_locations.append(location)
        
        # Add the directory to plugin_dirs for compatibility
        if location.enabled and os.path.isdir(location.path):
            self.add_plugin_directory(location.path)
        
        # Save the updated locations
        self._save_plugin_locations()
    
    def remove_plugin_location(self, location_id: str):
        """Remove a plugin location."""
        for i, location in enumerate(self.plugin_locations):
            if location.id == location_id:
                # Remove the location
                removed = self.plugin_locations.pop(i)
                
                # Remove the directory from plugin_dirs for compatibility
                if removed.path in self.plugin_dirs:
                    self.plugin_dirs.remove(removed.path)
                
                # Save the updated locations
                self._save_plugin_locations()
                return True
        
        return False
    
    def get_plugin_locations(self) -> List[PluginLocation]:
        """Get all plugin locations."""
        return self.plugin_locations
    
    def get_plugin_location(self, location_id: str) -> Optional[PluginLocation]:
        """Get a specific plugin location."""
        for location in self.plugin_locations:
            if location.id == location_id:
                return location
        return None
    
    def enable_plugin_location(self, location_id: str) -> bool:
        """Enable a plugin location."""
        location = self.get_plugin_location(location_id)
        if location:
            location.enabled = True
            
            # Add the directory to plugin_dirs for compatibility
            if os.path.isdir(location.path) and location.path not in self.plugin_dirs:
                self.add_plugin_directory(location.path)
            
            # Save the updated locations
            self._save_plugin_locations()
            return True
        
        return False
    
    def disable_plugin_location(self, location_id: str) -> bool:
        """Disable a plugin location."""
        location = self.get_plugin_location(location_id)
        if location:
            location.enabled = False
            
            # Remove the directory from plugin_dirs for compatibility
            if location.path in self.plugin_dirs:
                self.plugin_dirs.remove(location.path)
            
            # Save the updated locations
            self._save_plugin_locations()
            return True
        
        return False
    
    def set_auto_discovery(self, enabled: bool):
        """Enable or disable auto-discovery of plugins."""
        self.auto_discovery_enabled = enabled
        self.config.set_setting("plugins.auto_discovery", enabled)
        self.config.save()
    
    def is_auto_discovery_enabled(self) -> bool:
        """Check if auto-discovery is enabled."""
        return self.auto_discovery_enabled
    
    def discover_plugins(self) -> List[EnhancedPluginManifest]:
        """Discover plugins in all enabled locations."""
        discovered = []
        
        # Skip if auto-discovery is disabled
        if not self.auto_discovery_enabled:
            return discovered
        
        # Sort locations by priority
        locations = sorted(self.plugin_locations, key=lambda loc: loc.priority)
        
        # Discover plugins in each location
        for location in locations:
            if location.enabled and location.auto_discover:
                try:
                    # Discover plugins in the location
                    location_plugins = self._discover_plugins_in_location(location)
                    discovered.extend(location_plugins)
                except Exception as e:
                    logger.error(f"Error discovering plugins in location {location.id}: {e}", exc_info=True)
        
        return discovered
    
    def _discover_plugins_in_location(self, location: PluginLocation) -> List[EnhancedPluginManifest]:
        """Discover plugins in a specific location."""
        discovered = []
        
        if not os.path.isdir(location.path):
            return discovered
        
        # Look for plugin directories
        for item in os.listdir(location.path):
            item_path = os.path.join(location.path, item)
            
            # Skip files
            if not os.path.isdir(item_path):
                # Check if it's a plugin zip file
                if item.endswith(".zip") and os.path.isfile(item_path):
                    try:
                        # Extract manifest from zip
                        manifest = self._extract_manifest_from_zip(item_path)
                        if manifest:
                            manifest.path = item_path
                            discovered.append(manifest)
                    except Exception as e:
                        logger.error(f"Error extracting manifest from zip {item_path}: {e}", exc_info=True)
                continue
            
            # Check for manifest.json
            manifest_path = os.path.join(item_path, "manifest.json")
            if os.path.isfile(manifest_path):
                try:
                    # Load manifest
                    with open(manifest_path, "r") as f:
                        manifest_data = json.load(f)
                    
                    # Create manifest object
                    manifest = EnhancedPluginManifest.from_dict(manifest_data)
                    manifest.path = item_path
                    discovered.append(manifest)
                except Exception as e:
                    logger.error(f"Error loading manifest from {manifest_path}: {e}", exc_info=True)
            else:
                # Check for __init__.py (legacy plugin)
                init_path = os.path.join(item_path, "__init__.py")
                if os.path.isfile(init_path):
                    # Create a synthetic manifest
                    manifest = EnhancedPluginManifest(
                        id=item,
                        name=item,
                        version="1.0.0",
                        description="Legacy plugin",
                        author="Unknown",
                        plugin_type=PluginType.OTHER,
                        main_class="__init__"
                    )
                    manifest.path = item_path
                    discovered.append(manifest)
        
        return discovered
    
    def _extract_manifest_from_zip(self, zip_path: str) -> Optional[EnhancedPluginManifest]:
        """Extract manifest from a plugin zip file."""
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_file:
                # Check if manifest.json exists
                if "manifest.json" in zip_file.namelist():
                    # Extract manifest
                    with zip_file.open("manifest.json") as f:
                        manifest_data = json.loads(f.read().decode("utf-8"))
                    
                    # Create manifest object
                    manifest = EnhancedPluginManifest.from_dict(manifest_data)
                    return manifest
        except Exception as e:
            logger.error(f"Error extracting manifest from zip {zip_path}: {e}", exc_info=True)
        
        return None
    
    def install_plugin_from_zip(self, zip_path: str, location_id: str = None) -> bool:
        """Install a plugin from a zip file."""
        try:
            # Extract manifest
            manifest = self._extract_manifest_from_zip(zip_path)
            if not manifest:
                logger.error(f"No manifest found in zip {zip_path}")
                return False
            
            # Determine target location
            target_location = None
            if location_id:
                target_location = self.get_plugin_location(location_id)
            
            if not target_location:
                # Use the first enabled user location
                for location in self.plugin_locations:
                    if location.enabled and location.id != "builtin":
                        target_location = location
                        break
            
            if not target_location:
                logger.error("No suitable location found for plugin installation")
                return False
            
            # Create target directory
            target_dir = os.path.join(target_location.path, manifest.id)
            if os.path.exists(target_dir):
                # Remove existing directory
                shutil.rmtree(target_dir)
            
            # Extract zip to target directory
            with zipfile.ZipFile(zip_path, "r") as zip_file:
                zip_file.extractall(target_dir)
            
            logger.info(f"Installed plugin {manifest.id} to {target_dir}")
            return True
        
        except Exception as e:
            logger.error(f"Error installing plugin from zip {zip_path}: {e}", exc_info=True)
            return False
    
    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin."""
        try:
            # Get the plugin
            plugin = self.get_plugin(plugin_id)
            if not plugin:
                logger.error(f"Plugin {plugin_id} not found")
                return False
            
            # Check if the plugin is loaded
            if plugin_id in self.plugins:
                # Disable the plugin first
                self.disable_plugin(plugin_id)
            
            # Get the plugin directory
            plugin_dir = None
            if hasattr(plugin, "_location") and plugin._location:
                plugin_dir = os.path.join(plugin._location.path, plugin_id)
            elif hasattr(plugin, "manifest") and plugin.manifest and hasattr(plugin.manifest, "path"):
                plugin_dir = plugin.manifest.path
            
            if not plugin_dir or not os.path.isdir(plugin_dir):
                logger.error(f"Plugin directory not found for {plugin_id}")
                return False
            
            # Remove the plugin directory
            shutil.rmtree(plugin_dir)
            
            logger.info(f"Uninstalled plugin {plugin_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error uninstalling plugin {plugin_id}: {e}", exc_info=True)
            return False
    
    def _start_update_checker(self):
        """Start the plugin update checker."""
        # Create and start the update checker thread
        self.plugin_update_checker = threading.Thread(
            target=self._update_checker_thread,
            daemon=True
        )
        self.plugin_update_checker.start()
    
    def _update_checker_thread(self):
        """Thread function for checking plugin updates."""
        while True:
            try:
                # Check for updates
                self._check_for_plugin_updates()
            except Exception as e:
                logger.error(f"Error checking for plugin updates: {e}", exc_info=True)
            
            # Sleep for 24 hours
            time.sleep(24 * 60 * 60)
    
    def _check_for_plugin_updates(self):
        """Check for plugin updates."""
        # Get all plugins
        plugins = self.get_all_plugins()
        
        for plugin_id, plugin in plugins.items():
            try:
                # Check if the plugin has an update URL
                if (hasattr(plugin, "manifest") and plugin.manifest and 
                    hasattr(plugin.manifest, "update_url") and plugin.manifest.update_url):
                    
                    # TODO: Implement actual update checking logic
                    # For now, just log that we would check for updates
                    logger.info(f"Would check for updates for plugin {plugin_id} at {plugin.manifest.update_url}")
            except Exception as e:
                logger.error(f"Error checking for updates for plugin {plugin_id}: {e}", exc_info=True)
    
    def load_plugins(self):
        """Load all plugins from the configured directories."""
        # First, discover plugins
        discovered_manifests = self.discover_plugins()
        
        # Sort manifests by dependencies
        sorted_manifests = self._sort_manifests_by_dependencies(discovered_manifests)
        
        # Load each plugin
        for manifest in sorted_manifests:
            try:
                # Skip disabled plugins
                disabled_plugins = self.config.get_setting("plugins.disabled", [])
                if manifest.id in disabled_plugins:
                    logger.info(f"Skipping disabled plugin: {manifest.id}")
                    continue
                
                # Load the plugin
                self._load_enhanced_plugin(manifest)
            except Exception as e:
                logger.error(f"Error loading plugin {manifest.id}: {e}", exc_info=True)
                self.failed_plugins[manifest.id] = str(e)
        
        # Activate plugins
        for plugin_id, plugin in self.plugins.items():
            try:
                # Activate the plugin
                plugin.activate()
                logger.info(f"Activated plugin: {plugin_id}")
            except Exception as e:
                logger.error(f"Error activating plugin {plugin_id}: {e}", exc_info=True)
                self.failed_plugins[plugin_id] = str(e)
    
    def _load_enhanced_plugin(self, manifest):
        """Load a plugin from its manifest with enhanced functionality."""
        try:
            # Get the plugin directory
            plugin_dir = manifest.path
            
            # Check if it's a zip file
            if plugin_dir.endswith(".zip") and os.path.isfile(plugin_dir):
                # Extract to temporary directory if not already cached
                if plugin_dir not in self.plugin_zip_cache:
                    temp_dir = tempfile.mkdtemp(prefix=f"toolbar_plugin_{manifest.id}_")
                    with zipfile.ZipFile(plugin_dir, "r") as zip_file:
                        zip_file.extractall(temp_dir)
                    self.plugin_zip_cache[plugin_dir] = temp_dir
                
                # Use the extracted directory
                plugin_dir = self.plugin_zip_cache[plugin_dir]
            
            # Import the main module
            main_module_path = os.path.join(plugin_dir, manifest.main_class.replace(".", "/") + ".py")
            if not os.path.isfile(main_module_path):
                main_module_path = os.path.join(plugin_dir, "__init__.py")
                if not os.path.isfile(main_module_path):
                    raise ImportError(f"Main module not found: {manifest.main_class}")
            
            # Load the module
            module_name = f"toolkit.plugins.{manifest.id}"
            spec = importlib.util.spec_from_file_location(module_name, main_module_path)
            if spec is None:
                raise ImportError(f"Failed to create spec for {main_module_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the main class
            main_class_name = manifest.main_class.split(".")[-1]
            main_class = None
            
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj is not Plugin and
                    name == main_class_name):
                    main_class = obj
                    break
            
            if main_class is None:
                raise ImportError(f"Main class not found: {main_class_name}")
            
            # Create plugin instance
            plugin_instance = main_class()
            plugin_instance.manifest = manifest
            
            # Set plugin location if it's an EnhancedPlugin
            if isinstance(plugin_instance, EnhancedPlugin):
                # Find the location this plugin came from
                for location in self.plugin_locations:
                    if plugin_dir.startswith(location.path):
                        plugin_instance.set_location(location)
                        break
            
            # Initialize the plugin
            plugin_instance.initialize(self.config, self.event_bus, self.toolbar)
            
            # Add to plugins dictionary
            self.plugins[manifest.id] = plugin_instance
            
            logger.info(f"Loaded plugin: {manifest.id} v{manifest.version}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading plugin {manifest.id}: {e}", exc_info=True)
            self.failed_plugins[manifest.id] = str(e)
            return False
    
    def get_plugins_by_extended_type(self, plugin_type: ExtendedPluginType) -> Dict[str, Plugin]:
        """Get all plugins of a specific extended type."""
        result = {}
        
        for name, plugin in self.plugins.items():
            if (plugin.manifest and 
                hasattr(plugin.manifest, "plugin_type") and 
                plugin.manifest.plugin_type == plugin_type):
                result[name] = plugin
        
        return result
    
    def get_prompt_plugins(self) -> Dict[str, PromptPlugin]:
        """Get all prompt plugins."""
        result = {}
        
        for name, plugin in self.plugins.items():
            if isinstance(plugin, PromptPlugin):
                result[name] = plugin
        
        return result
    
    def get_scripting_plugins(self) -> Dict[str, ScriptingPlugin]:
        """Get all scripting plugins."""
        result = {}
        
        for name, plugin in self.plugins.items():
            if isinstance(plugin, ScriptingPlugin):
                result[name] = plugin
        
        return result
