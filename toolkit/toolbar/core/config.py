#!/usr/bin/env python3
import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Singleton instance
_config_instance = None

class Config:
    """
    Configuration manager for the Toolbar application.
    Handles loading, saving, and accessing configuration settings.
    """
    
    def __init__(self, config_file=None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file. If None, uses default location.
        """
        self.config_file = config_file or os.path.join(
            os.path.expanduser("~"), 
            ".config", 
            "toolkit", 
            "config.json"
        )
        self.settings = {}
        self.load()
    
    def load(self):
        """Load configuration from file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Load configuration if file exists
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    self.settings = json.load(f)
                logger.info(f"Configuration loaded from {self.config_file}")
            else:
                # Create default configuration
                self.settings = {
                    "auto_start": False,
                    "minimize_to_tray": True,
                    "plugins": {
                        "enabled": [],
                        "disabled": []
                    },
                    "github": {
                        "token": "",
                        "username": "",
                        "repositories": []
                    },
                    "linear": {
                        "api_key": "",
                        "team_id": ""
                    },
                    "ui": {
                        "theme": "system",
                        "font_size": 12,
                        "toolbar_position": "top"
                    }
                }
                self.save()
                logger.info(f"Default configuration created at {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
            # Use default configuration
            self.settings = {
                "auto_start": False,
                "minimize_to_tray": True,
                "plugins": {
                    "enabled": [],
                    "disabled": []
                }
            }
    
    def save(self):
        """Save configuration to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Save configuration
            with open(self.config_file, "w") as f:
                json.dump(self.settings, f, indent=4)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
    
    def get_setting(self, key, default=None):
        """
        Get a configuration setting.
        
        Args:
            key: Setting key (can use dot notation for nested settings)
            default: Default value if setting doesn't exist
        
        Returns:
            Setting value or default
        """
        try:
            # Handle nested settings with dot notation
            if "." in key:
                parts = key.split(".")
                value = self.settings
                for part in parts:
                    if part not in value:
                        return default
                    value = value[part]
                return value
            
            # Handle simple settings
            return self.settings.get(key, default)
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}", exc_info=True)
            return default
    
    def set_setting(self, key, value):
        """
        Set a configuration setting.
        
        Args:
            key: Setting key (can use dot notation for nested settings)
            value: Setting value
        """
        try:
            # Handle nested settings with dot notation
            if "." in key:
                parts = key.split(".")
                target = self.settings
                for part in parts[:-1]:
                    if part not in target:
                        target[part] = {}
                    target = target[part]
                target[parts[-1]] = value
            else:
                # Handle simple settings
                self.settings[key] = value
            
            # Save configuration
            self.save()
        except Exception as e:
            logger.error(f"Error setting {key} to {value}: {e}", exc_info=True)
    
    def get_plugin_setting(self, plugin_name, key, default=None):
        """
        Get a plugin-specific setting.
        
        Args:
            plugin_name: Name of the plugin
            key: Setting key
            default: Default value if setting doesn't exist
        
        Returns:
            Setting value or default
        """
        try:
            # Get plugin settings
            plugin_settings = self.settings.get("plugins", {}).get(plugin_name, {})
            
            # Return setting or default
            return plugin_settings.get(key, default)
        except Exception as e:
            logger.error(f"Error getting plugin setting {plugin_name}.{key}: {e}", exc_info=True)
            return default
    
    def set_plugin_setting(self, plugin_name, key, value):
        """
        Set a plugin-specific setting.
        
        Args:
            plugin_name: Name of the plugin
            key: Setting key
            value: Setting value
        """
        try:
            # Ensure plugins section exists
            if "plugins" not in self.settings:
                self.settings["plugins"] = {}
            
            # Ensure plugin section exists
            if plugin_name not in self.settings["plugins"]:
                self.settings["plugins"][plugin_name] = {}
            
            # Set setting
            self.settings["plugins"][plugin_name][key] = value
            
            # Save configuration
            self.save()
        except Exception as e:
            logger.error(f"Error setting plugin setting {plugin_name}.{key} to {value}: {e}", exc_info=True)
    
    def is_plugin_enabled(self, plugin_name):
        """
        Check if a plugin is enabled.
        
        Args:
            plugin_name: Name of the plugin
        
        Returns:
            True if plugin is enabled, False otherwise
        """
        try:
            # Get enabled and disabled plugins
            enabled = self.settings.get("plugins", {}).get("enabled", [])
            disabled = self.settings.get("plugins", {}).get("disabled", [])
            
            # Check if plugin is explicitly enabled or disabled
            if plugin_name in enabled:
                return True
            if plugin_name in disabled:
                return False
            
            # Default to enabled
            return True
        except Exception as e:
            logger.error(f"Error checking if plugin {plugin_name} is enabled: {e}", exc_info=True)
            return True
    
    def enable_plugin(self, plugin_name):
        """
        Enable a plugin.
        
        Args:
            plugin_name: Name of the plugin
        """
        try:
            # Ensure plugins section exists
            if "plugins" not in self.settings:
                self.settings["plugins"] = {}
            
            # Ensure enabled and disabled lists exist
            if "enabled" not in self.settings["plugins"]:
                self.settings["plugins"]["enabled"] = []
            if "disabled" not in self.settings["plugins"]:
                self.settings["plugins"]["disabled"] = []
            
            # Enable plugin
            if plugin_name not in self.settings["plugins"]["enabled"]:
                self.settings["plugins"]["enabled"].append(plugin_name)
            
            # Remove from disabled list
            if plugin_name in self.settings["plugins"]["disabled"]:
                self.settings["plugins"]["disabled"].remove(plugin_name)
            
            # Save configuration
            self.save()
        except Exception as e:
            logger.error(f"Error enabling plugin {plugin_name}: {e}", exc_info=True)
    
    def disable_plugin(self, plugin_name):
        """
        Disable a plugin.
        
        Args:
            plugin_name: Name of the plugin
        """
        try:
            # Ensure plugins section exists
            if "plugins" not in self.settings:
                self.settings["plugins"] = {}
            
            # Ensure enabled and disabled lists exist
            if "enabled" not in self.settings["plugins"]:
                self.settings["plugins"]["enabled"] = []
            if "disabled" not in self.settings["plugins"]:
                self.settings["plugins"]["disabled"] = []
            
            # Disable plugin
            if plugin_name not in self.settings["plugins"]["disabled"]:
                self.settings["plugins"]["disabled"].append(plugin_name)
            
            # Remove from enabled list
            if plugin_name in self.settings["plugins"]["enabled"]:
                self.settings["plugins"]["enabled"].remove(plugin_name)
            
            # Save configuration
            self.save()
        except Exception as e:
            logger.error(f"Error disabling plugin {plugin_name}: {e}", exc_info=True)

def get_config_instance(config_file=None):
    """
    Get the singleton configuration instance.
    
    Args:
        config_file: Path to the configuration file. If None, uses default location.
    
    Returns:
        Configuration instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config(config_file)
    
    return _config_instance
