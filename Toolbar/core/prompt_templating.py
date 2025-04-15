"""
Prompt templating module for the Toolbar application.
This module provides classes for creating and managing prompt templates.
"""

import re
import os
import json
import logging
from typing import Dict, List, Optional, Set

# Set up logging
logger = logging.getLogger(__name__)

class PromptTemplate:
    """
    Class representing a prompt template with variable substitution.
    """
    
    def __init__(self, name: str, content: str, shortcut: Optional[str] = None):
        """
        Initialize a prompt template.
        
        Args:
            name (str): Template name
            content (str): Template content with {variable} placeholders
            shortcut (str, optional): Keyboard shortcut for the template
        """
        self.name = name
        self.content = content
        self.shortcut = shortcut
    
    def get_variables(self) -> Set[str]:
        """
        Extract variable names from the template content.
        
        Returns:
            Set[str]: Set of variable names
        """
        # Find all {variable} patterns in the content
        pattern = r'\{([a-zA-Z0-9_]+)\}'
        return set(re.findall(pattern, self.content))
    
    def fill_template(self, variables: Dict[str, str]) -> str:
        """
        Fill the template with the provided variables.
        
        Args:
            variables (Dict[str, str]): Dictionary of variable names and values
            
        Returns:
            str: Filled template content
        """
        filled_content = self.content
        
        # Replace each {variable} with its value
        for var_name, var_value in variables.items():
            filled_content = filled_content.replace(f"{{{var_name}}}", var_value)
        
        return filled_content
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert the template to a dictionary for serialization.
        
        Returns:
            Dict[str, str]: Dictionary representation of the template
        """
        return {
            "name": self.name,
            "content": self.content,
            "shortcut": self.shortcut
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'PromptTemplate':
        """
        Create a template from a dictionary.
        
        Args:
            data (Dict[str, str]): Dictionary representation of the template
            
        Returns:
            PromptTemplate: New template instance
        """
        return cls(
            name=data.get("name", ""),
            content=data.get("content", ""),
            shortcut=data.get("shortcut")
        )

class PromptTemplateManager:
    """
    Manager for prompt templates.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the template manager.
        
        Args:
            config_file (str, optional): Path to the templates configuration file
        """
        self.templates: List[PromptTemplate] = []
        self.config_file = config_file or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "templates.json"
        )
        
        # Load templates from file
        self.load_templates()
    
    def load_templates(self) -> None:
        """Load templates from the configuration file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Convert dictionaries to PromptTemplate objects
                self.templates = [
                    PromptTemplate.from_dict(template_data)
                    for template_data in data.get("templates", [])
                ]
                
                logger.info(f"Loaded {len(self.templates)} templates from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load templates: {e}")
                self.templates = []
    
    def save_templates(self) -> None:
        """Save templates to the configuration file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Convert templates to dictionaries
            data = {
                "templates": [
                    template.to_dict()
                    for template in self.templates
                ]
            }
            
            # Write to file
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=4)
            
            logger.info(f"Saved {len(self.templates)} templates to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")
    
    def get_templates(self) -> List[PromptTemplate]:
        """
        Get all templates.
        
        Returns:
            List[PromptTemplate]: List of all templates
        """
        return self.templates
    
    def get_template(self, index: int) -> Optional[PromptTemplate]:
        """
        Get a template by index.
        
        Args:
            index (int): Template index
            
        Returns:
            Optional[PromptTemplate]: Template at the given index, or None if not found
        """
        if 0 <= index < len(self.templates):
            return self.templates[index]
        return None
    
    def add_template(self, template: PromptTemplate) -> None:
        """
        Add a new template.
        
        Args:
            template (PromptTemplate): Template to add
        """
        self.templates.append(template)
        self.save_templates()
    
    def update_template(self, index: int, template: PromptTemplate) -> bool:
        """
        Update an existing template.
        
        Args:
            index (int): Index of the template to update
            template (PromptTemplate): Updated template
            
        Returns:
            bool: True if successful, False otherwise
        """
        if 0 <= index < len(self.templates):
            self.templates[index] = template
            self.save_templates()
            return True
        return False
    
    def remove_template(self, index: int) -> bool:
        """
        Remove a template.
        
        Args:
            index (int): Index of the template to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        if 0 <= index < len(self.templates):
            self.templates.pop(index)
            self.save_templates()
            return True
        return False
    
    def get_template_by_name(self, name: str) -> Optional[PromptTemplate]:
        """
        Get a template by name.
        
        Args:
            name (str): Template name
            
        Returns:
            Optional[PromptTemplate]: Template with the given name, or None if not found
        """
        for template in self.templates:
            if template.name == name:
                return template
        return None
    
    def get_template_by_shortcut(self, shortcut: str) -> Optional[PromptTemplate]:
        """
        Get a template by shortcut.
        
        Args:
            shortcut (str): Template shortcut
            
        Returns:
            Optional[PromptTemplate]: Template with the given shortcut, or None if not found
        """
        for template in self.templates:
            if template.shortcut == shortcut:
                return template
        return None
