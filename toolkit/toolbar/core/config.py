#!/usr/bin/env python3
import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
import appdirs

logger = logging.getLogger(__name__)

# Singleton instance
_config_instance = None

def get_config_instance():
    """Get the singleton Config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

class Config:
    """Configuration manager for the Toolbar application."""
    
    def __init__(self, config_file=None):
        """Initialize the configuration manager."""
        self.settings = {}
        
        # Set default config file path if not provided
        if config_file is None:
            config_dir = appdirs.user_config_dir("toolkit", "zeeeepa")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "config.json")
        
        self.config_file = config_file
        
        # Load configuration
        self.load()
        
        # Set default settings
        self._set_defaults()
    
    def _set_defaults(self):
        """Set default settings if they don't exist."""
        defaults = {
            "ui.theme": "dark",
            "ui.position": "bottom",
            "ui.always_on_top": True,
            "ui.show_clock": True,
            "ui.show_notifications": True,
            "ui.taskbar_height": 48,
            "ui.button_size": 32,
            "ui.button_spacing": 4,
            "ui.font_size": 10,
            "ui.font_family": "Arial",
            "ui.opacity": 1.0,
            "ui.auto_hide": False,
            "ui.auto_hide_delay": 3000,
            "plugins.enabled": True,
            "plugins.auto_update": True,
            "plugins.user_dir": os.path.join(appdirs.user_data_dir("toolkit", "zeeeepa"), "plugins"),
            "plugins.disabled": [],
            "system.auto_start": False,
            "system.check_updates": True,
            "system.update_interval": 86400,  # 24 hours in seconds
            "system.log_level": "INFO",
            "system.log_file": os.path.join(appdirs.user_log_dir("toolkit", "zeeeepa"), "toolkit.log"),
            "system.debug_mode": False,
            "apps.favorites": [],
            "apps.recent": [],
            "apps.max_recent": 10,
        }
        
        # Set defaults for any missing settings
        for key, value in defaults.items():
            if not self.has_setting(key):
                self.set_setting(key, value)
    
    def load(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    self.settings = json.load(f)
                logger.info(f"Configuration loaded from {self.config_file}")
            else:
                logger.info(f"Configuration file {self.config_file} not found, using defaults")
                self.settings = {}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
            self.settings = {}
    
    def save(self):
        """Save configuration to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, "w") as f:
                json.dump(self.settings, f, indent=4)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            return False
    
    def get_setting(self, key, default=None):
        """
        Get a setting value.
        
        Args:
            key: Setting key (dot-separated path)
            default: Default value if setting doesn't exist
        
        Returns:
            Setting value or default
        """
        # Handle dot notation (e.g., "ui.theme")
        if "." in key:
            parts = key.split(".")
            current = self.settings
            
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    return default
                current = current[part]
            
            return current.get(parts[-1], default)
        
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        """
        Set a setting value.
        
        Args:
            key: Setting key (dot-separated path)
            value: Setting value
        """
        # Handle dot notation (e.g., "ui.theme")
        if "." in key:
            parts = key.split(".")
            current = self.settings
            
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    current[part] = {}
                
                current = current[part]
            
            current[parts[-1]] = value
        else:
            self.settings[key] = value
    
    def has_setting(self, key):
        """
        Check if a setting exists.
        
        Args:
            key: Setting key (dot-separated path)
        
        Returns:
            True if setting exists, False otherwise
        """
        # Handle dot notation (e.g., "ui.theme")
        if "." in key:
            parts = key.split(".")
            current = self.settings
            
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    return False
                current = current[part]
            
            return parts[-1] in current
        
        return key in self.settings
    
    def delete_setting(self, key):
        """
        Delete a setting.
        
        Args:
            key: Setting key (dot-separated path)
        
        Returns:
            True if setting was deleted, False otherwise
        """
        # Handle dot notation (e.g., "ui.theme")
        if "." in key:
            parts = key.split(".")
            current = self.settings
            
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    return False
                current = current[part]
            
            if parts[-1] in current:
                del current[parts[-1]]
                return True
            
            return False
        
        if key in self.settings:
            del self.settings[key]
            return True
        
        return False
    
    def get_all_settings(self):
        """
        Get all settings.
        
        Returns:
            Dictionary of all settings
        """
        return self.settings.copy()
    
    def add_favorite_app(self, app_info):
        """
        Add an application to favorites.
        
        Args:
            app_info: Dictionary with app information (name, path, icon, args)
        """
        favorites = self.get_setting("apps.favorites", [])
        
        # Check if app is already in favorites
        for i, app in enumerate(favorites):
            if app.get("path") == app_info.get("path"):
                # Update existing app
                favorites[i] = app_info
                self.set_setting("apps.favorites", favorites)
                return
        
        # Add new app
        favorites.append(app_info)
        self.set_setting("apps.favorites", favorites)
    
    def remove_favorite_app(self, app_path):
        """
        Remove an application from favorites.
        
        Args:
            app_path: Path of the application to remove
        
        Returns:
            True if app was removed, False otherwise
        """
        favorites = self.get_setting("apps.favorites", [])
        
        for i, app in enumerate(favorites):
            if app.get("path") == app_path:
                favorites.pop(i)
                self.set_setting("apps.favorites", favorites)
                return True
        
        return False
    
    def add_recent_app(self, app_info):
        """
        Add an application to recent apps.
        
        Args:
            app_info: Dictionary with app information (name, path, icon, args)
        """
        recent = self.get_setting("apps.recent", [])
        max_recent = self.get_setting("apps.max_recent", 10)
        
        # Remove app if already in recent list
        recent = [app for app in recent if app.get("path") != app_info.get("path")]
        
        # Add app to beginning of list
        recent.insert(0, app_info)
        
        # Trim list if needed
        if len(recent) > max_recent:
            recent = recent[:max_recent]
        
        self.set_setting("apps.recent", recent)
    
    def clear_recent_apps(self):
        """Clear the recent apps list."""
        self.set_setting("apps.recent", [])
