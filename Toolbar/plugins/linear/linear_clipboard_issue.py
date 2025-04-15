#!/usr/bin/env python3
import sys
import time
import warnings
import keyboard
import pyperclip
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

# Add parent directory to path
sys.path.insert(0, '..')

# Import custom modules
from Toolbar.core.config import Config
from Toolbar.core.linear_integration import LinearIntegration, LinearIssue
from Toolbar.ui.linear_settings import LinearTemplateDialog

# Suppress PyQt5 deprecation warnings
warnings.filterwarnings("ignore", message=".*sipPyTypeDict.*")

class LinearClipboardIssue:
    """
    Tool to create Linear issues from clipboard content.
    """
    def __init__(self):
        """Initialize the Linear clipboard issue tool."""
        # Create application
        self.app = QApplication(sys.argv)
        
        # Initialize configuration
        self.config = Config()
        
        # Initialize Linear integration
        self.linear_integration = LinearIntegration(self.config)
        
        # Register keyboard shortcut
        keyboard.add_hotkey('ctrl+shift+alt+c', self.handle_shortcut)
        
        # Start the application
        sys.exit(self.app.exec_())
    
    def handle_shortcut(self):
        """Handle the keyboard shortcut."""
        # Wait 0.3 seconds
        time.sleep(0.3)
        
        # Get clipboard content
        clipboard_content = pyperclip.paste()
        
        if not clipboard_content:
            QMessageBox.warning(None, "Empty Clipboard", "Clipboard is empty.")
            return
        
        # Show template dialog
        self.show_template_dialog(clipboard_content)
    
    def show_template_dialog(self, content):
        """
        Show the template dialog.
        
        Args:
            content (str): Clipboard content
        """
        # Create dialog
        dialog = LinearTemplateDialog(self.linear_integration)
        
        # Connect signal
        dialog.template_selected.connect(lambda template: self.create_issue(content, template))
        
        # Show dialog
        dialog.exec_()
    
    def create_issue(self, content, template):
        """
        Create a Linear issue from clipboard content and template.
        
        Args:
            content (str): Clipboard content
            template (dict): Template dictionary
        """
        # Get template content
        template_content = template.get('content', '')
        
        # Replace placeholder with clipboard content
        description = template_content.replace('{clipboard}', content)
        
        # Create issue
        issue = LinearIssue(
            title=f"Issue from clipboard: {content[:50]}{'...' if len(content) > 50 else ''}",
            description=description
        )
        
        # Send to Linear
        result = self.linear_integration.create_issue(issue)
        
        if result:
            QMessageBox.information(
                None, 
                "Issue Created", 
                f"Linear issue created successfully.\n\nTitle: {result['title']}\n\nURL: {result['url']}"
            )
        else:
            QMessageBox.warning(
                None, 
                "Error", 
                "Failed to create Linear issue. Please check your API key and settings."
            )

if __name__ == "__main__":
    LinearClipboardIssue()
