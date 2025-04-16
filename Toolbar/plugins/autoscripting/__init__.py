"""
Autoscripting plugin for the Toolbar application.
This plugin provides a framework for creating and running automation scripts.
"""

import os
import sys
import json
import logging
import importlib.util
import inspect
from typing import Dict, List, Any, Optional, Callable

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget

# Import from Toolbar core
from Toolbar.core.enhanced_plugin_system import ScriptingPlugin, EnhancedPlugin
from Toolbar.core.plugin_system import Plugin, PluginType

logger = logging.getLogger(__name__)

class Script:
    """Class representing an automation script."""
    
    def __init__(self, script_id: str, name: str, description: str, code: str, 
                 author: str = "", version: str = "1.0.0", tags: List[str] = None):
        """Initialize a script."""
        self.id = script_id
        self.name = name
        self.description = description
        self.code = code
        self.author = author
        self.version = version
        self.tags = tags or []
        self.compiled = None
    
    def compile(self):
        """Compile the script code."""
        try:
            self.compiled = compile(self.code, f"<script_{self.id}>", "exec")
            return True
        except Exception as e:
            logger.error(f"Error compiling script {self.id}: {e}", exc_info=True)
            return False
    
    def run(self, globals_dict: Dict[str, Any] = None, locals_dict: Dict[str, Any] = None) -> Any:
        """Run the script."""
        if not self.compiled and not self.compile():
            return None
        
        # Create execution environment
        globals_dict = globals_dict or {}
        locals_dict = locals_dict or {}
        
        # Add script metadata to globals
        globals_dict.update({
            "__script_id__": self.id,
            "__script_name__": self.name,
            "__script_version__": self.version,
            "__script_author__": self.author
        })
        
        try:
            # Execute the script
            exec(self.compiled, globals_dict, locals_dict)
            
            # Return the result if available
            return locals_dict.get("result", None)
        except Exception as e:
            logger.error(f"Error running script {self.id}: {e}", exc_info=True)
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "author": self.author,
            "version": self.version,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Script':
        """Create a Script from a dictionary."""
        return cls(
            script_id=data.get("id"),
            name=data.get("name"),
            description=data.get("description", ""),
            code=data.get("code", ""),
            author=data.get("author", ""),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", [])
        )

class ScriptManager:
    """Manager for automation scripts."""
    
    def __init__(self, scripts_dir: str = None):
        """Initialize the script manager."""
        self.scripts = {}
        self.scripts_dir = scripts_dir or os.path.expanduser("~/.toolbar/scripts")
        
        # Create scripts directory if it doesn't exist
        os.makedirs(self.scripts_dir, exist_ok=True)
        
        # Load scripts
        self.load_scripts()
    
    def load_scripts(self):
        """Load scripts from the scripts directory."""
        try:
            # Clear existing scripts
            self.scripts = {}
            
            # Load scripts from directory
            for filename in os.listdir(self.scripts_dir):
                if filename.endswith(".json"):
                    try:
                        # Load script from file
                        script_path = os.path.join(self.scripts_dir, filename)
                        with open(script_path, "r") as f:
                            script_data = json.load(f)
                        
                        # Create script object
                        script = Script.from_dict(script_data)
                        
                        # Add to scripts dictionary
                        self.scripts[script.id] = script
                    except Exception as e:
                        logger.error(f"Error loading script {filename}: {e}", exc_info=True)
            
            logger.info(f"Loaded {len(self.scripts)} scripts")
        except Exception as e:
            logger.error(f"Error loading scripts: {e}", exc_info=True)
    
    def save_script(self, script: Script) -> bool:
        """Save a script to file."""
        try:
            # Create script file path
            script_path = os.path.join(self.scripts_dir, f"{script.id}.json")
            
            # Save script to file
            with open(script_path, "w") as f:
                json.dump(script.to_dict(), f, indent=2)
            
            # Add to scripts dictionary
            self.scripts[script.id] = script
            
            logger.info(f"Saved script {script.id}")
            return True
        except Exception as e:
            logger.error(f"Error saving script {script.id}: {e}", exc_info=True)
            return False
    
    def delete_script(self, script_id: str) -> bool:
        """Delete a script."""
        try:
            # Check if script exists
            if script_id not in self.scripts:
                logger.warning(f"Script {script_id} not found")
                return False
            
            # Create script file path
            script_path = os.path.join(self.scripts_dir, f"{script_id}.json")
            
            # Delete script file
            if os.path.isfile(script_path):
                os.remove(script_path)
            
            # Remove from scripts dictionary
            del self.scripts[script_id]
            
            logger.info(f"Deleted script {script_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting script {script_id}: {e}", exc_info=True)
            return False
    
    def get_script(self, script_id: str) -> Optional[Script]:
        """Get a script by ID."""
        return self.scripts.get(script_id)
    
    def get_scripts(self) -> List[Script]:
        """Get all scripts."""
        return list(self.scripts.values())
    
    def run_script(self, script_id: str, globals_dict: Dict[str, Any] = None, 
                  locals_dict: Dict[str, Any] = None) -> Any:
        """Run a script by ID."""
        script = self.get_script(script_id)
        if not script:
            logger.warning(f"Script {script_id} not found")
            return None
        
        return script.run(globals_dict, locals_dict)

class AutoScriptingPlugin(Plugin):
    """Plugin for automated scripting functionality."""
    
    def __init__(self):
        super().__init__()
        self._name = "AutoScripting"
        self._version = "1.0.0"
        self._description = "Automated scripting functionality"
    
    def initialize(self, config, event_bus=None, toolbar=None):
        """Initialize the plugin."""
        super().initialize(config, event_bus, toolbar)
        return True
    
    def get_icon(self):
        """Get the plugin icon."""
        return QIcon.fromTheme("applications-system")
    
    def get_title(self):
        """Get the plugin title."""
        return "Scripts"
