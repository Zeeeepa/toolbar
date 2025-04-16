#!/usr/bin/env python3
import os
import sys
import logging
from typing import Dict, List, Any, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox, QCheckBox, QTabWidget
)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """Dialog for configuring toolbar settings."""
    
    def __init__(self, parent=None):
        """Initialize the settings dialog."""
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Toolbar Settings")
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the settings dialog UI."""
        layout = QVBoxLayout()
        
        # Create tab widget
        tabs = QTabWidget()
        
        # General settings tab
        general_tab = QDialog()
        general_layout = QVBoxLayout()
        
        # Position settings
        position_group = QHBoxLayout()
        position_label = QLabel("Screen Position:")
        self.position_x = QSpinBox()
        self.position_y = QSpinBox()
        position_group.addWidget(position_label)
        position_group.addWidget(self.position_x)
        position_group.addWidget(self.position_y)
        general_layout.addLayout(position_group)
        
        # Size settings
        size_group = QHBoxLayout()
        size_label = QLabel("Window Size:")
        self.width_spin = QSpinBox()
        self.height_spin = QSpinBox()
        size_group.addWidget(size_label)
        size_group.addWidget(self.width_spin)
        size_group.addWidget(self.height_spin)
        general_layout.addLayout(size_group)
        
        # Opacity setting
        opacity_group = QHBoxLayout()
        opacity_label = QLabel("Opacity:")
        self.opacity_spin = QSpinBox()
        self.opacity_spin.setRange(10, 100)
        self.opacity_spin.setSingleStep(5)
        opacity_group.addWidget(opacity_label)
        opacity_group.addWidget(self.opacity_spin)
        general_layout.addLayout(opacity_group)
        
        # Always on top
        self.always_on_top = QCheckBox("Always on Top")
        general_layout.addWidget(self.always_on_top)
        
        general_tab.setLayout(general_layout)
        tabs.addTab(general_tab, "General")
        
        # Add tabs to main layout
        layout.addWidget(tabs)
        
        # Dialog buttons
        button_box = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        save_button.clicked.connect(self.save_settings)
        cancel_button.clicked.connect(self.reject)
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)
        
        self.setLayout(layout)
        
    def save_settings(self):
        """Save the current settings and close dialog."""
        # Get values from UI elements
        settings = {
            'position': (self.position_x.value(), self.position_y.value()),
            'size': (self.width_spin.value(), self.height_spin.value()),
            'opacity': self.opacity_spin.value() / 100.0,
            'always_on_top': self.always_on_top.isChecked()
        }
        
        # Update parent toolbar with new settings
        if self.parent:
            self.parent.apply_settings(settings)
        
        self.accept()
        
    def load_settings(self, settings):
        """Load existing settings into the dialog."""
        if 'position' in settings:
            self.position_x.setValue(settings['position'][0])
            self.position_y.setValue(settings['position'][1])
        if 'size' in settings:
            self.width_spin.setValue(settings['size'][0])
            self.height_spin.setValue(settings['size'][1])
        if 'opacity' in settings:
            self.opacity_spin.setValue(int(settings['opacity'] * 100))
        if 'always_on_top' in settings:
            self.always_on_top.setChecked(settings['always_on_top'])
