"""
Example Plugin for the Toolbar application.
This plugin demonstrates the dynamic plugin loading system.
"""

import os
import json
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QIcon
from Toolbar.core.plugin_system import Plugin

logger = logging.getLogger(__name__)

class ExamplePlugin(Plugin):
    """Example plugin that demonstrates the plugin system."""
    
    def __init__(self):
        super().__init__()
        self.config = None
        self.settings = {}
        self.ui_widget = None
        
    def initialize(self, config):
        """Initialize the plugin with the given configuration."""
        self.config = config
        
        # Load settings from metadata.json if available
        metadata_path = os.path.join(os.path.dirname(__file__), "metadata.json")
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    self.settings = metadata.get("settings", {})
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
        
        logger.info(f"Example Plugin initialized with settings: {self.settings}")
    
    def cleanup(self):
        """Clean up resources used by the plugin."""
        logger.info("Example Plugin cleaned up")
    
    def get_icon(self):
        """Get the icon for the plugin to display in the taskbar."""
        # Use a default icon from the system theme
        return QIcon.fromTheme("help-about")
    
    def get_title(self):
        """Get the title for the plugin to display in the taskbar."""
        return "Example Plugin"
    
    def activate(self):
        """Activate the plugin when its taskbar button is clicked."""
        logger.info("Example Plugin activated")
        
        # Create a simple UI widget if it doesn't exist
        if not self.ui_widget:
            self.ui_widget = QWidget()
            self.ui_widget.setWindowTitle("Example Plugin")
            self.ui_widget.resize(300, 200)
            
            layout = QVBoxLayout(self.ui_widget)
            
            # Add a label
            label = QLabel("This is an example plugin that demonstrates the dynamic plugin loading system.")
            label.setWordWrap(True)
            layout.addWidget(label)
            
            # Add a button
            button = QPushButton("Click Me")
            button.clicked.connect(self._on_button_clicked)
            layout.addWidget(button)
        
        # Show the widget
        self.ui_widget.show()
        self.ui_widget.raise_()
    
    def _on_button_clicked(self):
        """Handle button click event."""
        logger.info("Example Plugin button clicked")
        if self.ui_widget:
            label = QLabel("Button clicked!")
            self.ui_widget.layout().addWidget(label)
    
    @property
    def name(self):
        """Get the name of the plugin."""
        return "Example Plugin"
    
    @property
    def version(self):
        """Get the version of the plugin."""
        return "1.0.0"
    
    @property
    def description(self):
        """Get the description of the plugin."""
        return "An example plugin that demonstrates the dynamic plugin loading system."
    
    @property
    def dependencies(self):
        """Get the list of plugin dependencies."""
        return []
