#!/usr/bin/env python3
import os
import logging
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from toolkit.toolbar.core.plugin_system import Plugin

logger = logging.getLogger(__name__)

class ExamplePlugin(Plugin):
    """Example plugin to demonstrate the plugin system."""
    
    def __init__(self):
        super().__init__()
        self.dialog = None
    
    def initialize(self, config):
        """Initialize the plugin."""
        self.config = config
        logger.info("Example plugin initialized")
    
    def cleanup(self):
        """Clean up resources."""
        if self.dialog:
            self.dialog.close()
            self.dialog = None
        logger.info("Example plugin cleaned up")
    
    def get_icon(self):
        """Get the icon for the plugin."""
        return QIcon.fromTheme("help-about", QIcon())
    
    def get_title(self):
        """Get the title for the plugin."""
        return "Example"
    
    def activate(self):
        """Activate the plugin."""
        if not self.dialog:
            self.dialog = ExampleDialog()
        
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
        
        logger.info("Example plugin activated")
    
    @property
    def name(self):
        return "ExamplePlugin"
    
    @property
    def version(self):
        return "1.0.0"
    
    @property
    def description(self):
        return "An example plugin to demonstrate the plugin system."

class ExampleDialog(QDialog):
    """Dialog for the example plugin."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Example Plugin")
        self.setMinimumSize(400, 300)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add title
        title_label = QLabel("Example Plugin")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Add description
        desc_label = QLabel("This is an example plugin to demonstrate the plugin system.")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Add text area
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Type something here...")
        layout.addWidget(self.text_edit)
        
        # Add buttons
        buttons_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_text)
        buttons_layout.addWidget(self.clear_button)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_text)
        buttons_layout.addWidget(self.save_button)
        
        layout.addLayout(buttons_layout)
    
    def clear_text(self):
        """Clear the text area."""
        self.text_edit.clear()
    
    def save_text(self):
        """Save the text to a file."""
        try:
            # Get text
            text = self.text_edit.toPlainText()
            
            # Save to file
            home_dir = os.path.expanduser("~")
            file_path = os.path.join(home_dir, "example_plugin_text.txt")
            
            with open(file_path, "w") as f:
                f.write(text)
            
            # Show success message
            self.text_edit.setPlainText(f"Text saved to {file_path}")
        except Exception as e:
            # Show error message
            self.text_edit.setPlainText(f"Error saving text: {str(e)}")
