"""
Prompt templating module for the Toolbar application.
This module provides classes for creating and managing prompt templates.
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional, Any

# Set up logging
logger = logging.getLogger(__name__)

class PromptTemplate:
    """
    Class for managing prompt templates.
    """
    
    def __init__(self, name: str, content: str, variables: Optional[List[str]] = None, description: str = ""):
        """
        Initialize a prompt template.
        
        Args:
            name: Name of the template
            content: Template content with variable placeholders
            variables: List of variable names used in the template
            description: Description of the template
        """
        self.name = name
        self.content = content
        self.description = description
        
        # Extract variables from content if not provided
        if variables is None:
            self.variables = self._extract_variables(content)
        else:
            self.variables = variables
    
    def _extract_variables(self, content: str) -> List[str]:
        """
        Extract variable names from template content.
        
        Args:
            content: Template content
            
        Returns:
            List of variable names
        """
        # Find all {{variable}} patterns
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, content)
        
        # Remove duplicates and strip whitespace
        variables = list(set([var.strip() for var in matches]))
        
        return variables
    
    def render(self, variables: Dict[str, str]) -> str:
        """
        Render the template with the provided variables.
        
        Args:
            variables: Dictionary of variable names and values
            
        Returns:
            Rendered template
        """
        result = self.content
        
        # Replace each variable
        for var_name, var_value in variables.items():
            result = result.replace(f"{{{{{var_name}}}}}", var_value)
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert template to dictionary for serialization.
        
        Returns:
            Dictionary representation of the template
        """
        return {
            "name": self.name,
            "content": self.content,
            "variables": self.variables,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """
        Create a template from dictionary.
        
        Args:
            data: Dictionary representation of the template
            
        Returns:
            PromptTemplate instance
        """
        return cls(
            name=data.get("name", ""),
            content=data.get("content", ""),
            variables=data.get("variables", []),
            description=data.get("description", "")
        )

class PromptTemplateManager:
    """
    Manager for prompt templates.
    """
    
    def __init__(self, config_file: str = None):
        """
        Initialize the prompt template manager.
        
        Args:
            config_file: Path to the configuration file
        """
        self.templates: Dict[str, PromptTemplate] = {}
        self.config_file = config_file or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "templates.json"
        )
        
        # Create default templates
        self._create_default_templates()
        
        # Load templates from file
        self.load_templates()
    
    def _create_default_templates(self):
        """Create default templates."""
        # GitHub PR template
        self.templates["github_pr"] = PromptTemplate(
            name="GitHub PR",
            content="""Title: {{title}}

## Description
{{description}}

## Changes
{{changes}}

## Testing
{{testing}}

## Screenshots
{{screenshots}}

## Checklist
- [ ] I have tested these changes
- [ ] I have updated the documentation
- [ ] I have added tests
""",
            description="Template for GitHub pull requests"
        )
        
        # Linear issue template
        self.templates["linear_issue"] = PromptTemplate(
            name="Linear Issue",
            content="""## Description
{{description}}

## Acceptance Criteria
{{acceptance_criteria}}

## Steps to Reproduce
{{steps_to_reproduce}}

## Expected Behavior
{{expected_behavior}}

## Actual Behavior
{{actual_behavior}}
""",
            description="Template for Linear issues"
        )
        
        # Code review template
        self.templates["code_review"] = PromptTemplate(
            name="Code Review",
            content="""## Code Review

### Overall Impression
{{overall_impression}}

### Strengths
{{strengths}}

### Areas for Improvement
{{areas_for_improvement}}

### Questions
{{questions}}

### Suggestions
{{suggestions}}
""",
            description="Template for code reviews"
        )
    
    def load_templates(self):
        """Load templates from configuration file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Load templates
                for template_data in data.get("templates", []):
                    template = PromptTemplate.from_dict(template_data)
                    self.templates[template.name] = template
                
                logger.info(f"Loaded {len(self.templates)} templates from {self.config_file}")
            except Exception as e:
                logger.error(f"Error loading templates: {e}", exc_info=True)
    
    def save_templates(self):
        """Save templates to configuration file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Convert templates to list of dictionaries
            templates_data = [template.to_dict() for template in self.templates.values()]
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump({"templates": templates_data}, f, indent=4)
            
            logger.info(f"Saved {len(self.templates)} templates to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving templates: {e}", exc_info=True)
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """
        Get a template by name.
        
        Args:
            name: Name of the template
            
        Returns:
            PromptTemplate instance or None if not found
        """
        return self.templates.get(name)
    
    def add_template(self, template: PromptTemplate) -> bool:
        """
        Add a new template.
        
        Args:
            template: PromptTemplate instance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.templates[template.name] = template
            self.save_templates()
            return True
        except Exception as e:
            logger.error(f"Error adding template: {e}", exc_info=True)
            return False
    
    def update_template(self, name: str, template: PromptTemplate) -> bool:
        """
        Update an existing template.
        
        Args:
            name: Name of the template to update
            template: Updated PromptTemplate instance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if name in self.templates:
                self.templates[name] = template
                self.save_templates()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating template: {e}", exc_info=True)
            return False
    
    def remove_template(self, name: str) -> bool:
        """
        Remove a template.
        
        Args:
            name: Name of the template to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if name in self.templates:
                del self.templates[name]
                self.save_templates()
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing template: {e}", exc_info=True)
            return False
    
    def get_all_templates(self) -> List[PromptTemplate]:
        """
        Get all templates.
        
        Returns:
            List of all PromptTemplate instances
        """
        return list(self.templates.values())
    
    def render_template(self, name: str, variables: Dict[str, str]) -> Optional[str]:
        """
        Render a template with the provided variables.
        
        Args:
            name: Name of the template
            variables: Dictionary of variable names and values
            
        Returns:
            Rendered template or None if template not found
        """
        template = self.get_template(name)
        if template:
            return template.render(variables)
        return None
