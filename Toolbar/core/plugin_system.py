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
from typing import Dict, List, Any, Optional, Type, Callable, Set, Union
from enum import Enum
from dataclasses import dataclass
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

# Define plugin states
class PluginState(Enum):
    """Enum representing the possible states of a plugin."""
    UNLOADED = "unloaded"
    LOADED = "loaded"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"
    ERROR = "error"

# Define plugin types
class PluginType(Enum):
    """Enum representing the types of plugins."""
    CORE = "core"
    UI = "ui"
    INTEGRATION = "integration"
    AUTOMATION = "automation"
    UTILITY = "utility"
    OTHER = "other"

@dataclass
class PluginDependency:
    """Class representing a plugin dependency."""
    plugin_id: str
    version_requirement: str = "*"
    optional: bool = False

@dataclass
class PluginManifest:
    """Class representing a plugin manifest."""
    id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    main_class: str
    dependencies: List[PluginDependency] = None
    min_toolbar_version: str = "1.0.0"
    max_toolbar_version: str = "*"
    settings_schema: Dict[str, Any] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginManifest':
        """Create a PluginManifest from a dictionary."""
        # Convert plugin_type string to enum
        plugin_type = PluginType(data.get("plugin_type", "other"))
        
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
            settings_schema=data.get("settings_schema")
        )

class PluginEvent(QObject):
    """Base class for plugin events."""
    def __init__(self, event_type: str, source_plugin_id: str, data: Any = None):
        super().__init__()
        self.event_type = event_type
        self.source_plugin_id = source_plugin_id
        self.data = data
        self.timestamp = time.time()

class EventBus(QObject):
    """Event bus for plugin communication."""
    event_received = pyqtSignal(PluginEvent)
    
    def __init__(self):
        super().__init__()
        self.subscribers = {}
    
    def publish(self, event: PluginEvent):
        """Publish an event to all subscribers."""
        logger.debug(f"Publishing event: {event.event_type} from {event.source_plugin_id}")
        self.event_received.emit(event)
        
        # Notify subscribers
        if event.event_type in self.subscribers:
            for callback in self.subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in event subscriber: {e}", exc_info=True)
    
    def subscribe(self, event_type: str, callback: Callable[[PluginEvent], None]):
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = set()
        self.subscribers[event_type].add(callback)
        logger.debug(f"Subscribed to event: {event_type}")
        
        return lambda: self.unsubscribe(event_type, callback)
    
    def unsubscribe(self, event_type: str, callback: Callable[[PluginEvent], None]):
        """Unsubscribe from an event type."""
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            logger.debug(f"Unsubscribed from event: {event_type}")
            
            # Clean up empty subscriber sets
            if not self.subscribers[event_type]:
                del self.subscribers[event_type]

class Plugin:
    """Enhanced base class for all plugins."""
    
    def __init__(self):
        """Initialize the plugin."""
        self._state = PluginState.UNLOADED
        self._manifest = None
        self._event_bus = None
        self._config = None
        self._subscriptions = []
        self._toolbar = None
    
    def initialize(self, config, event_bus=None, toolbar=None):
        """Initialize the plugin with the given configuration and event bus."""
        self._config = config
        self._event_bus = event_bus
        self._toolbar = toolbar
        self._state = PluginState.LOADED
        return True
    
    def activate(self):
        """Activate the plugin. Called after all dependencies are loaded."""
        self._state = PluginState.ACTIVATED
        return True
    
    def deactivate(self):
        """Deactivate the plugin but keep it loaded."""
        self._state = PluginState.DEACTIVATED
        return True
    
    def cleanup(self):
        """Clean up resources used by the plugin."""
        # Unsubscribe from all events
        for unsubscribe in self._subscriptions:
            unsubscribe()
        self._subscriptions = []
        return True
    
    def get_icon(self):
        """Get the icon for the plugin to display in the taskbar."""
        from PyQt5.QtGui import QIcon
        return QIcon.fromTheme("application-x-executable")
    
    def get_title(self):
        """Get the title for the plugin to display in the taskbar."""
        return self.name
    
    def get_settings_ui(self):
        """Get the settings UI for the plugin."""
        return None
    
    def publish_event(self, event_type: str, data: Any = None):
        """Publish an event to the event bus."""
        if self._event_bus:
            event = PluginEvent(event_type, self.id, data)
            self._event_bus.publish(event)
    
    def subscribe_to_event(self, event_type: str, callback: Callable[[PluginEvent], None]):
        """Subscribe to an event type."""
        if self._event_bus:
            unsubscribe = self._event_bus.subscribe(event_type, callback)
            self._subscriptions.append(unsubscribe)
            return unsubscribe
        return lambda: None
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a plugin-specific setting."""
        if self._config:
            return self._config.get_setting(f"plugins.{self.id}.{key}", default)
        return default
    
    def set_setting(self, key: str, value: Any):
        """Set a plugin-specific setting."""
        if self._config:
            self._config.set_setting(f"plugins.{self.id}.{key}", value)
    
    @property
    def id(self) -> str:
        """Get the ID of the plugin."""
        return self._manifest.id if self._manifest else self.__class__.__name__
    
    @property
    def name(self) -> str:
        """Get the name of the plugin."""
        return self._manifest.name if self._manifest else self.__class__.__name__
    
    @property
    def version(self) -> str:
        """Get the version of the plugin."""
        return self._manifest.version if self._manifest else "1.0.0"
    
    @property
    def description(self) -> str:
        """Get the description of the plugin."""
        return self._manifest.description if self._manifest else "No description provided."
    
    @property
    def state(self) -> PluginState:
        """Get the current state of the plugin."""
        return self._state
    
    @property
    def manifest(self) -> PluginManifest:
        """Get the plugin manifest."""
        return self._manifest
    
    @manifest.setter
    def manifest(self, manifest: PluginManifest):
        """Set the plugin manifest."""
        self._manifest = manifest

# Define specific plugin interfaces
class GitHubPlugin(Plugin):
    """Interface for GitHub plugins."""
    
    def get_repositories(self) -> List[Dict[str, Any]]:
        """Get the list of GitHub repositories."""
        return []
    
    def get_pull_requests(self, repo: str) -> List[Dict[str, Any]]:
        """Get the list of pull requests for a repository."""
        return []
    
    def create_pull_request(self, repo: str, title: str, body: str, head: str, base: str) -> Dict[str, Any]:
        """Create a pull request."""
        return {}
    
    def get_notifications(self) -> List[Dict[str, Any]]:
        """Get GitHub notifications."""
        return []

class LinearPlugin(Plugin):
    """Interface for Linear plugins."""
    
    def get_teams(self) -> List[Dict[str, Any]]:
        """Get the list of Linear teams."""
        return []
    
    def get_projects(self, team_id: str = None) -> List[Dict[str, Any]]:
        """Get the list of Linear projects."""
        return []
    
    def get_issues(self, team_id: str = None, project_id: str = None) -> List[Dict[str, Any]]:
        """Get the list of Linear issues."""
        return []
    
    def create_issue(self, team_id: str, title: str, description: str = None) -> Dict[str, Any]:
        """Create a Linear issue."""
        return {}
    
    def get_issue_details(self, issue_id: str) -> Dict[str, Any]:
        """Get details for a specific issue."""
        return {}

class AutomationPlugin(Plugin):
    """Interface for automation plugins."""
    
    def get_scripts(self) -> List[Dict[str, Any]]:
        """Get the list of automation scripts."""
        return []
    
    def run_script(self, script_id: str, params: Dict[str, Any] = None) -> Any:
        """Run an automation script."""
        return None
    
    def create_script(self, name: str, content: str, description: str = None) -> Dict[str, Any]:
        """Create a new automation script."""
        return {}

class PromptPlugin(Plugin):
    """Interface for prompt template plugins."""
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """Get the list of prompt templates."""
        return []
    
    def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get a specific prompt template."""
        return {}
    
    def create_template(self, name: str, content: str, variables: List[str] = None) -> Dict[str, Any]:
        """Create a new prompt template."""
        return {}
    
    def fill_template(self, template_id: str, variables: Dict[str, str]) -> str:
        """Fill a template with variables."""
        return ""

class PluginManager:
    """Enhanced manager for loading and accessing plugins."""
    
    def __init__(self, config):
        """Initialize the plugin manager with the given configuration."""
        self.config = config
        self.plugins = {}
        self.plugin_dirs = []
        self.failed_plugins = {}
        self.event_bus = EventBus()
        self.toolbar = None
        
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
    
    def set_toolbar(self, toolbar):
        """Set the toolbar instance for plugins to access."""
        self.toolbar = toolbar
    
    def load_plugins(self):
        """Load all plugins from the plugin directories."""
        # Clear existing plugins
        self.plugins = {}
        self.failed_plugins = {}
        
        # Get disabled plugins from config
        disabled_plugins = self.config.get_setting("plugins.disabled", [])
        
        # Discover plugins and their manifests
        plugin_manifests = self._discover_plugins(disabled_plugins)
        
        # Sort plugins by dependencies
        sorted_manifests = self._sort_plugins_by_dependencies(plugin_manifests)
        
        # Load plugins in dependency order
        for manifest in sorted_manifests:
            self._load_plugin(manifest)
        
        # Activate plugins in dependency order
        for manifest in sorted_manifests:
            plugin_id = manifest.id
            if plugin_id in self.plugins and self.plugins[plugin_id].state == PluginState.LOADED:
                try:
                    self.plugins[plugin_id].activate()
                    logger.info(f"Activated plugin: {plugin_id}")
                except Exception as e:
                    logger.error(f"Error activating plugin {plugin_id}: {e}", exc_info=True)
                    self.failed_plugins[plugin_id] = str(e)
        
        logger.info(f"Loaded {len(self.plugins)} plugins")
        if self.failed_plugins:
            logger.warning(f"Failed to load {len(self.failed_plugins)} plugins")
    
    def _discover_plugins(self, disabled_plugins):
        """Discover plugins and their manifests."""
        manifests = []
        
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
                
                # Look for manifest.json
                manifest_path = os.path.join(item_path, "manifest.json")
                if os.path.isfile(manifest_path):
                    try:
                        with open(manifest_path, "r") as f:
                            manifest_data = json.load(f)
                        
                        # Create manifest object
                        manifest = PluginManifest.from_dict(manifest_data)
                        manifest.path = item_path
                        
                        manifests.append(manifest)
                        logger.info(f"Discovered plugin: {manifest.id} v{manifest.version}")
                    except Exception as e:
                        logger.error(f"Error loading manifest for {item}: {e}", exc_info=True)
                        self.failed_plugins[item] = f"Invalid manifest: {str(e)}"
                else:
                    # Legacy plugin without manifest
                    try:
                        # Try to load as a legacy plugin
                        self._load_legacy_plugin(item_path, item)
                    except Exception as e:
                        logger.error(f"Error loading legacy plugin {item}: {e}", exc_info=True)
                        self.failed_plugins[item] = str(e)
        
        return manifests
    
    def _sort_plugins_by_dependencies(self, manifests):
        """Sort plugins by dependencies using topological sort."""
        # Create a graph of dependencies
        graph = {}
        for manifest in manifests:
            graph[manifest.id] = []
            
            # Add dependencies
            if manifest.dependencies:
                for dep in manifest.dependencies:
                    if not dep.optional:
                        graph[manifest.id].append(dep.plugin_id)
        
        # Perform topological sort
        result = []
        visited = set()
        temp_visited = set()
        
        def visit(node):
            if node in temp_visited:
                raise ValueError(f"Circular dependency detected: {node}")
            
            if node not in visited:
                temp_visited.add(node)
                
                # Visit dependencies
                for neighbor in graph.get(node, []):
                    visit(neighbor)
                
                temp_visited.remove(node)
                visited.add(node)
                
                # Find the manifest for this node
                for manifest in manifests:
                    if manifest.id == node:
                        result.append(manifest)
                        break
        
        # Visit all nodes
        for manifest in manifests:
            if manifest.id not in visited:
                visit(manifest.id)
        
        return result
    
    def _load_plugin(self, manifest):
        """Load a plugin from its manifest."""
        try:
            # Get the plugin directory
            plugin_dir = manifest.path
            
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
    
    def _load_legacy_plugin(self, plugin_dir, plugin_name):
        """Load a legacy plugin without a manifest."""
        # Look for __init__.py
        init_path = os.path.join(plugin_dir, "__init__.py")
        if not os.path.isfile(init_path):
            logger.warning(f"Plugin {plugin_name} has no __init__.py file")
            return
        
        # Load the module
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
                
                # Create a synthetic manifest
                manifest = PluginManifest(
                    id=plugin_name,
                    name=getattr(plugin_instance, "name", plugin_name),
                    version=getattr(plugin_instance, "version", "1.0.0"),
                    description=getattr(plugin_instance, "description", "Legacy plugin"),
                    author="Unknown",
                    plugin_type=PluginType.OTHER,
                    main_class=plugin_class.__name__
                )
                manifest.path = plugin_dir
                plugin_instance.manifest = manifest
                
                try:
                    # Initialize the plugin
                    plugin_instance.initialize(self.config, self.event_bus, self.toolbar)
                    self.plugins[plugin_instance.id] = plugin_instance
                    logger.info(f"Loaded legacy plugin: {plugin_instance.id} v{plugin_instance.version}")
                except Exception as e:
                    logger.error(f"Error initializing legacy plugin {plugin_instance.id}: {e}", exc_info=True)
                    self.failed_plugins[plugin_instance.id] = str(e)
        
        except Exception as e:
            logger.error(f"Error loading legacy plugin module {plugin_name}: {e}", exc_info=True)
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
    
    def get_plugins_by_type(self, plugin_type):
        """Get all plugins of a specific type."""
        return {name: plugin for name, plugin in self.plugins.items() 
                if plugin.manifest and plugin.manifest.plugin_type == plugin_type}
    
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
                # Deactivate the plugin first
                if self.plugins[name].state == PluginState.ACTIVATED:
                    self.plugins[name].deactivate()
                
                # Clean up the plugin
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
    
    def reload_plugin(self, name):
        """Reload a specific plugin."""
        if name in self.plugins:
            try:
                # Deactivate and clean up the plugin
                if self.plugins[name].state == PluginState.ACTIVATED:
                    self.plugins[name].deactivate()
                self.plugins[name].cleanup()
                
                # Get the manifest
                manifest = self.plugins[name].manifest
                
                # Remove from plugins dictionary
                del self.plugins[name]
                
                # Reload the plugin
                success = self._load_plugin(manifest)
                
                if success and name in self.plugins:
                    # Activate the plugin
                    self.plugins[name].activate()
                    logger.info(f"Reloaded plugin: {name}")
                    return True
            except Exception as e:
                logger.error(f"Error reloading plugin {name}: {e}", exc_info=True)
                self.failed_plugins[name] = str(e)
        
        return False
    
    def cleanup(self):
        """Clean up all plugins."""
        for name, plugin in list(self.plugins.items()):
            try:
                # Deactivate the plugin first
                if plugin.state == PluginState.ACTIVATED:
                    plugin.deactivate()
                
                # Clean up the plugin
                plugin.cleanup()
                logger.info(f"Cleaned up plugin: {name}")
            except Exception as e:
                logger.error(f"Error cleaning up plugin {name}: {e}", exc_info=True)
        
        self.plugins = {}
