"""
Prompt Template plugin for the Toolbar application.
This plugin provides prompt template management and application.
"""

from Toolbar.core.plugin_system import Plugin, PromptPlugin
from Toolbar.plugins.templateprompt.prompt_templating import PromptTemplateManager

class PromptTemplatePlugin(PromptPlugin):
    """Prompt Template plugin."""
    
    def __init__(self):
        super().__init__()
        self.template_manager = None
    
    def initialize(self, config, event_bus=None, toolbar=None):
        """Initialize the Prompt Template plugin."""
        super().initialize(config, event_bus, toolbar)
        try:
            # Initialize template manager
            self.template_manager = PromptTemplateManager(config)
            
            # Subscribe to events
            if event_bus:
                self.subscribe_to_event("clipboard.copy", self._on_clipboard_copy)
                self.subscribe_to_event("ai.request", self._on_ai_request)
            
            return True
        except Exception as e:
            print(f"Failed to initialize Prompt Template plugin: {e}")
            return False
    
    def cleanup(self):
        """Clean up Prompt Template plugin resources."""
        # Unsubscribe from events is handled by the base class
        return super().cleanup()
    
    def get_templates(self):
        """Get the list of prompt templates."""
        if not self.template_manager:
            return []
        
        templates = []
        for i, template in enumerate(self.template_manager.get_templates()):
            templates.append({
                "id": str(i),
                "name": template.name,
                "content": template.content,
                "variables": template.get_variables()
            })
        
        return templates
    
    def get_template(self, template_id):
        """Get a specific prompt template."""
        if not self.template_manager:
            return {}
        
        try:
            index = int(template_id)
            template = self.template_manager.get_template(index)
            if template:
                return {
                    "id": template_id,
                    "name": template.name,
                    "content": template.content,
                    "variables": template.get_variables()
                }
        except (ValueError, IndexError):
            pass
        
        return {}
    
    def create_template(self, name, content, variables=None):
        """Create a new prompt template."""
        if not self.template_manager:
            return {}
        
        from Toolbar.plugins.templateprompt.prompt_templating import PromptTemplate
        
        template = PromptTemplate(name=name, content=content)
        success = self.template_manager.add_template(template)
        
        if success:
            return {
                "id": str(len(self.template_manager.get_templates()) - 1),
                "name": template.name,
                "content": template.content,
                "variables": template.get_variables()
            }
        
        return {}
    
    def fill_template(self, template_id, variables):
        """Fill a template with variables."""
        if not self.template_manager:
            return ""
        
        try:
            index = int(template_id)
            template = self.template_manager.get_template(index)
            if template:
                return template.fill_template(variables)
        except (ValueError, IndexError):
            pass
        
        return ""
    
    def get_settings_ui(self):
        """Get the settings UI for the plugin."""
        try:
            from Toolbar.plugins.templateprompt.ui.prompt_templating_ui import PromptTemplateSettingsUI
            return PromptTemplateSettingsUI(self.template_manager, self._config)
        except Exception as e:
            print(f"Error creating settings UI: {e}")
            return None
    
    def _on_clipboard_copy(self, event):
        """Handle clipboard copy event."""
        # Check if clipboard integration is enabled
        if not self.get_setting("clipboard_integration", True):
            return
        
        # Check if the clipboard content contains template variables
        clipboard_text = event.data.get("text", "")
        if not clipboard_text or "{" not in clipboard_text or "}" not in clipboard_text:
            return
        
        # TODO: Implement clipboard integration
        pass
    
    def _on_ai_request(self, event):
        """Handle AI request event."""
        # TODO: Implement AI request integration
        pass
