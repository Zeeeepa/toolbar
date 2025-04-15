#!/usr/bin/env python3
import os
import sys
import logging
from typing import Dict, List, Optional, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal

from toolkit.toolbar.core.plugin_system import Plugin

logger = logging.getLogger(__name__)

class ExamplePlugin(Plugin):
    """
    Example plugin for the Toolkit application.
    Demonstrates how to create a simple plugin with a UI.
    """
    
    def __init__(self):
        """Initialize the plugin."""
        super().__init__()
        self.config = None
        self.ui = None
    
    def initialize(self, config):
        """
        Initialize the plugin.
        
        Args:
            config: Configuration object
        """
        self.config = config
        logger.info("Example plugin initialized")
    
    def cleanup(self):
        """Clean up resources used by the plugin."""
        logger.info("Example plugin cleaned up")
    
    def get_ui(self):
        """
        Get the plugin UI.
        
        Returns:
            Plugin UI object
        """
        if self.ui is None:
            self.ui = ExamplePluginUI(self.config)
        return self.ui
    
    @property
    def name(self) -> str:
        """Get the name of the plugin."""
        return "ExamplePlugin"
    
    @property
    def version(self) -> str:
        """Get the version of the plugin."""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Get the description of the plugin."""
        return "Example plugin for the Toolkit application"

class ExamplePluginUI:
    """UI for the example plugin."""
    
    def __init__(self, config):
        """
        Initialize the plugin UI.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.widget = QWidget()
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Create layout
        layout = QVBoxLayout(self.widget)
        
        # Create title label
        title_label = QLabel("Example Plugin")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Create description label
        description_label = QLabel("This is an example plugin for the Toolkit application.")
        description_label.setWordWrap(True)
        layout.addWidget(description_label)
        
        # Create input field
        input_layout = QHBoxLayout()
        input_label = QLabel("Input:")
        self.input_field = QLineEdit()
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_field)
        layout.addLayout(input_layout)
        
        # Create button
        self.process_button = QPushButton("Process")
        self.process_button.clicked.connect(self._process_input)
        layout.addWidget(self.process_button)
        
        # Create output field
        output_label = QLabel("Output:")
        layout.addWidget(output_label)
        
        self.output_field = QTextEdit()
        self.output_field.setReadOnly(True)
        layout.addWidget(self.output_field)
        
        # Add spacer
        layout.addStretch()
    
    def _process_input(self):
        """Process the input and display the output."""
        try:
            # Get input
            input_text = self.input_field.text()
            
            # Process input
            output_text = f"Processed: {input_text}\n"
            output_text += f"Length: {len(input_text)} characters\n"
            output_text += f"Uppercase: {input_text.upper()}\n"
            output_text += f"Lowercase: {input_text.lower()}\n"
            
            # Display output
            self.output_field.setText(output_text)
            
            # Save to configuration
            self.config.set_plugin_setting("ExamplePlugin", "last_input", input_text)
            
            logger.info(f"Input processed: {input_text}")
        except Exception as e:
            logger.error(f"Error processing input: {e}", exc_info=True)
            self.output_field.setText(f"Error: {str(e)}")
    
    def get_widget(self):
        """
        Get the plugin widget.
        
        Returns:
            QWidget: Plugin widget
        """
        return self.widget
