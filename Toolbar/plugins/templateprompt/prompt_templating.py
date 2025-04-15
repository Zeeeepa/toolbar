import os
import json
import re
import warnings
from PyQt5.QtCore import QObject, pyqtSignal

# Suppress PyQt5 deprecation warnings
warnings.filterwarnings("ignore", message=".*sipPyTypeDict.*")

class PromptTemplate:
    """
    Class representing a prompt template with variables.
    """
    def __init__(self, name="", content="", shortcut=None):
        """
        Initialize a prompt template.
        
        Args:
            name (str): Template name
            content (str): Template content with variables in {variable_name} format
            shortcut (str, optional): Keyboard shortcut for the template
        """
        self.name = name
        self.content = content
        self.shortcut = shortcut
        
    def get_variables(self):
        """Extract variable names from the template content."""
        # Find all occurrences of {variable_name}
        variables = re.findall(r'\{([^{}]+)\}', self.content)
        # Remove duplicates and return as a list
        return list(set(variables))
    
    def fill_template(self, variables_dict=None):
        """
        Fill the template with values from provided dictionary or environment variables.
        
        Args:
            variables_dict (dict, optional): Dictionary of variable values
            
        Returns:
            str: Filled template content
        """
        # Start with the original content
        filled_content = self.content
        
        # Get all variables in the template
        template_variables = self.get_variables()
        
        # Replace each variable with its value
        for var in template_variables:
            # Try to get value from provided dictionary first
            if variables_dict and var in variables_dict:
                value = variables_dict[var]
            else:
                # Fall back to environment variables
                value = os.environ.get(var, "")
                
            filled_content = filled_content.replace(f"{{{var}}}", value)
            
        return filled_content
    
    def to_dict(self):
        """Convert template to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "content": self.content,
            "shortcut": self.shortcut
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a template from a dictionary."""
        return cls(
            name=data.get("name", ""),
            content=data.get("content", ""),
            shortcut=data.get("shortcut")
        )

class PromptTemplateManager(QObject):
    """
    Manager for prompt templates.
    """
    template_added = pyqtSignal(object)
    template_removed = pyqtSignal(str)
    template_updated = pyqtSignal(object)
    
    def __init__(self, config):
        """
        Initialize the prompt template manager.
        
        Args:
            config (Config): Application configuration
        """
        super().__init__()
        self.config = config
        self.templates = []
        self.templates_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompt_templates.json")
        
        # Load templates
        self.load_templates()
        
        # Load default prompts if no templates exist
        if not self.templates:
            self.load_default_prompts()
    
    def load_templates(self):
        """Load templates from JSON file."""
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'r') as f:
                    data = json.load(f)
                    
                    # Convert dictionaries to PromptTemplate objects
                    self.templates = [PromptTemplate.from_dict(item) for item in data]
            except Exception as e:
                warnings.warn(f"Failed to load templates: {str(e)}")
    
    def load_default_prompts(self):
        """Load default prompts from the Prompts directory."""
        prompts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Prompts")
        
        if os.path.exists(prompts_dir):
            try:
                # Get all prompt files
                prompt_files = [f for f in os.listdir(prompts_dir) if f.endswith('.prompt') or f.endswith('.promptp')]
                
                # Load each prompt file
                for prompt_file in prompt_files:
                    try:
                        file_path = os.path.join(prompts_dir, prompt_file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Create template name from file name
                        name = os.path.splitext(prompt_file)[0]
                        
                        # Create template
                        template = PromptTemplate(name=name, content=content)
                        
                        # Add to templates list
                        self.templates.append(template)
                    except Exception as e:
                        warnings.warn(f"Failed to load prompt file {prompt_file}: {str(e)}")
                
                # Save templates to JSON file
                self.save_templates()
            except Exception as e:
                warnings.warn(f"Failed to load default prompts: {str(e)}")
    
    def save_templates(self):
        """Save templates to JSON file."""
        try:
            # Convert PromptTemplate objects to dictionaries
            data = [template.to_dict() for template in self.templates]
            
            with open(self.templates_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            warnings.warn(f"Failed to save templates: {str(e)}")
    
    def add_template(self, template):
        """
        Add a new template.
        
        Args:
            template (PromptTemplate): Template to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.templates.append(template)
            self.save_templates()
            self.template_added.emit(template)
            return True
        except Exception as e:
            warnings.warn(f"Failed to add template: {str(e)}")
            return False
    
    def update_template(self, index, template):
        """
        Update an existing template.
        
        Args:
            index (int): Index of the template to update
            template (PromptTemplate): Updated template
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if 0 <= index < len(self.templates):
                self.templates[index] = template
                self.save_templates()
                self.template_updated.emit(template)
                return True
            return False
        except Exception as e:
            warnings.warn(f"Failed to update template: {str(e)}")
            return False
    
    def remove_template(self, index):
        """
        Remove a template.
        
        Args:
            index (int): Index of the template to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if 0 <= index < len(self.templates):
                template_name = self.templates[index].name
                self.templates.pop(index)
                self.save_templates()
                self.template_removed.emit(template_name)
                return True
            return False
        except Exception as e:
            warnings.warn(f"Failed to remove template: {str(e)}")
            return False
    
    def get_template(self, index):
        """
        Get a template by index.
        
        Args:
            index (int): Index of the template
            
        Returns:
            PromptTemplate: The template, or None if not found
        """
        if 0 <= index < len(self.templates):
            return self.templates[index]
        return None
    
    def get_template_by_name(self, name):
        """
        Get a template by name.
        
        Args:
            name (str): Name of the template
            
        Returns:
            PromptTemplate: The template, or None if not found
        """
        for template in self.templates:
            if template.name == name:
                return template
        return None
    
    def get_templates(self):
        """
        Get all templates.
        
        Returns:
            list: List of PromptTemplate objects
        """
        return self.templates
