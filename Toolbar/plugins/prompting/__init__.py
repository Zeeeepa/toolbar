"""
Prompting plugin for the Toolbar application.
This plugin provides a framework for creating and using prompt templates.
"""

import os
import sys
import json
import logging
import importlib.util
import inspect
from typing import Dict, List, Any, Optional, Callable
import re

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget

# Import from Toolbar core
from Toolbar.core.enhanced_plugin_system import PromptPlugin, EnhancedPlugin

logger = logging.getLogger(__name__)

class PromptTemplate:
    """Class representing a prompt template."""
    
    def __init__(self, template_id: str, name: str, description: str, template: str, 
                 variables: List[Dict[str, Any]] = None, author: str = "", 
                 version: str = "1.0.0", tags: List[str] = None, model: str = None):
        """Initialize a prompt template."""
        self.id = template_id
        self.name = name
        self.description = description
        self.template = template
        self.variables = variables or []
        self.author = author
        self.version = version
        self.tags = tags or []
        self.model = model
    
    def render(self, variables: Dict[str, Any]) -> str:
        """Render the template with variables."""
        result = self.template
        
        # Replace variables in the template
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            result = result.replace(placeholder, str(var_value))
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template": self.template,
            "variables": self.variables,
            "author": self.author,
            "version": self.version,
            "tags": self.tags,
            "model": self.model
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """Create a PromptTemplate from a dictionary."""
        return cls(
            template_id=data.get("id"),
            name=data.get("name"),
            description=data.get("description", ""),
            template=data.get("template", ""),
            variables=data.get("variables", []),
            author=data.get("author", ""),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
            model=data.get("model")
        )
    
    def extract_variables(self) -> List[str]:
        """Extract variable names from the template."""
        # Find all placeholders in the format {variable_name}
        pattern = r"\{([a-zA-Z0-9_]+)\}"
        matches = re.findall(pattern, self.template)
        
        # Return unique variable names
        return list(set(matches))

class TemplateManager:
    """Manager for prompt templates."""
    
    def __init__(self, templates_dir: str = None):
        """Initialize the template manager."""
        self.templates = {}
        self.templates_dir = templates_dir or os.path.expanduser("~/.toolbar/templates")
        
        # Create templates directory if it doesn't exist
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Load templates
        self.load_templates()
    
    def load_templates(self):
        """Load templates from the templates directory."""
        try:
            # Clear existing templates
            self.templates = {}
            
            # Load templates from directory
            for filename in os.listdir(self.templates_dir):
                if filename.endswith(".json"):
                    try:
                        # Load template from file
                        template_path = os.path.join(self.templates_dir, filename)
                        with open(template_path, "r") as f:
                            template_data = json.load(f)
                        
                        # Create template object
                        template = PromptTemplate.from_dict(template_data)
                        
                        # Add to templates dictionary
                        self.templates[template.id] = template
                    except Exception as e:
                        logger.error(f"Error loading template {filename}: {e}", exc_info=True)
            
            logger.info(f"Loaded {len(self.templates)} templates")
        except Exception as e:
            logger.error(f"Error loading templates: {e}", exc_info=True)
    
    def save_template(self, template: PromptTemplate) -> bool:
        """Save a template to file."""
        try:
            # Create template file path
            template_path = os.path.join(self.templates_dir, f"{template.id}.json")
            
            # Save template to file
            with open(template_path, "w") as f:
                json.dump(template.to_dict(), f, indent=2)
            
            # Add to templates dictionary
            self.templates[template.id] = template
            
            logger.info(f"Saved template {template.id}")
            return True
        except Exception as e:
            logger.error(f"Error saving template {template.id}: {e}", exc_info=True)
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        try:
            # Check if template exists
            if template_id not in self.templates:
                logger.warning(f"Template {template_id} not found")
                return False
            
            # Create template file path
            template_path = os.path.join(self.templates_dir, f"{template_id}.json")
            
            # Delete template file
            if os.path.isfile(template_path):
                os.remove(template_path)
            
            # Remove from templates dictionary
            del self.templates[template_id]
            
            logger.info(f"Deleted template {template_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {e}", exc_info=True)
            return False
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a template by ID."""
        return self.templates.get(template_id)
    
    def get_templates(self) -> List[PromptTemplate]:
        """Get all templates."""
        return list(self.templates.values())
    
    def render_template(self, template_id: str, variables: Dict[str, Any]) -> Optional[str]:
        """Render a template with variables."""
        template = self.get_template(template_id)
        if not template:
            logger.warning(f"Template {template_id} not found")
            return None
        
        return template.render(variables)

class PromptingPlugin(PromptPlugin):
    """Plugin for prompt templates."""
    
    def __init__(self):
        """Initialize the plugin."""
        super().__init__()
        self.template_manager = None
        self.ui = None
    
    def initialize(self, config, event_bus=None, toolbar=None):
        """Initialize the plugin."""
        super().initialize(config, event_bus, toolbar)
        
        # Create template manager
        templates_dir = self.get_setting("templates_dir", os.path.expanduser("~/.toolbar/templates"))
        self.template_manager = TemplateManager(templates_dir)
        
        # Create UI if toolbar is provided
        if toolbar:
            try:
                from Toolbar.plugins.prompting.ui.prompt_templating_ui import PromptTemplatingUI
                self.ui = PromptTemplatingUI(self, toolbar)
            except Exception as e:
                logger.error(f"Error creating prompt UI: {e}", exc_info=True)
        
        return True
    
    def activate(self):
        """Activate the plugin."""
        super().activate()
        
        # Show UI if available
        if self.ui:
            self.ui.show()
        
        return True
    
    def deactivate(self):
        """Deactivate the plugin."""
        # Hide UI if available
        if self.ui:
            self.ui.hide()
        
        return super().deactivate()
    
    def cleanup(self):
        """Clean up resources."""
        # Clean up UI
        if self.ui:
            self.ui.cleanup()
            self.ui = None
        
        return super().cleanup()
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """Get the list of prompt templates."""
        if not self.template_manager:
            return []
        
        return [template.to_dict() for template in self.template_manager.get_templates()]
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific prompt template."""
        if not self.template_manager:
            return None
        
        template = self.template_manager.get_template(template_id)
        return template.to_dict() if template else None
    
    def render_template(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Render a prompt template with variables."""
        if not self.template_manager:
            return ""
        
        return self.template_manager.render_template(template_id, variables) or ""
    
    def create_template(self, template: Dict[str, Any]) -> bool:
        """Create a new prompt template."""
        if not self.template_manager:
            return False
        
        # Create template object
        template_obj = PromptTemplate.from_dict(template)
        
        # Save the template
        return self.template_manager.save_template(template_obj)
    
    def update_template(self, template_id: str, template: Dict[str, Any]) -> bool:
        """Update an existing prompt template."""
        if not self.template_manager:
            return False
        
        # Check if template exists
        if not self.template_manager.get_template(template_id):
            return False
        
        # Create template object
        template_obj = PromptTemplate.from_dict(template)
        
        # Ensure ID is correct
        template_obj.id = template_id
        
        # Save the template
        return self.template_manager.save_template(template_obj)
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a prompt template."""
        if not self.template_manager:
            return False
        
        return self.template_manager.delete_template(template_id)
    
    def get_icon(self):
        """Get the icon for the plugin."""
        from PyQt5.QtGui import QIcon
        return QIcon.fromTheme("format-text-bold")
    
    def get_title(self):
        """Get the title for the plugin."""
        return "Prompts"
