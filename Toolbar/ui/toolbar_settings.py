#!/usr/bin/env python3
import os
import sys
import logging
from typing import Dict, List, Any, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QCheckBox, QGroupBox
)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """Dialog for configuring toolbar settings."""
    
    def __init__(self, parent=None):
        """Initialize the settings dialog."""
        super().__init__(parent)
        self.parent = parent
        self.config = parent.config if parent else None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the settings dialog UI."""
        self.setWindowTitle('Settings')
        layout = QVBoxLayout()

        # General Settings
        general_group = QGroupBox("General Settings")
        general_layout = QVBoxLayout()

        # Startup behavior
        startup_layout = QHBoxLayout()
        startup_label = QLabel("Start with Windows:")
        self.startup_checkbox = QCheckBox()
        self.startup_checkbox.setChecked(self.config.get("start_with_windows", False) if self.config else False)
        startup_layout.addWidget(startup_label)
        startup_layout.addWidget(self.startup_checkbox)
        startup_layout.addStretch()
        general_layout.addLayout(startup_layout)

        # Always on top
        ontop_layout = QHBoxLayout()
        ontop_label = QLabel("Always on top:")
        self.ontop_checkbox = QCheckBox()
        self.ontop_checkbox.setChecked(self.config.get("always_on_top", True) if self.config else True)
        ontop_layout.addWidget(ontop_label)
        ontop_layout.addWidget(self.ontop_checkbox)
        ontop_layout.addStretch()
        general_layout.addLayout(ontop_layout)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        # Plugin Settings
        plugin_group = QGroupBox("Plugin Settings")
        plugin_layout = QVBoxLayout()

        # Plugin directory
        plugin_dir_layout = QHBoxLayout()
        plugin_dir_label = QLabel("Plugin Directory:")
        self.plugin_dir_edit = QLineEdit()
        self.plugin_dir_edit.setText(self.config.get("plugin_dir", "") if self.config else "")
        plugin_dir_browse = QPushButton("Browse...")
        plugin_dir_layout.addWidget(plugin_dir_label)
        plugin_dir_layout.addWidget(self.plugin_dir_edit)
        plugin_dir_layout.addWidget(plugin_dir_browse)
        plugin_layout.addLayout(plugin_dir_layout)

        # Auto-load plugins
        autoload_layout = QHBoxLayout()
        autoload_label = QLabel("Auto-load plugins:")
        self.autoload_checkbox = QCheckBox()
        self.autoload_checkbox.setChecked(self.config.get("auto_load_plugins", True) if self.config else True)
        autoload_layout.addWidget(autoload_label)
        autoload_layout.addWidget(self.autoload_checkbox)
        autoload_layout.addStretch()
        plugin_layout.addLayout(autoload_layout)

        plugin_group.setLayout(plugin_layout)
        layout.addWidget(plugin_group)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        
    def save_settings(self):
        """Save the current settings and close dialog."""
        if not self.config:
            logger.warning("No config object available")
            self.reject()
            return

        try:
            self.config.set("start_with_windows", self.startup_checkbox.isChecked())
            self.config.set("always_on_top", self.ontop_checkbox.isChecked())
            self.config.set("plugin_dir", self.plugin_dir_edit.text())
            self.config.set("auto_load_plugins", self.autoload_checkbox.isChecked())
            self.config.save()
            
            if self.parent:
                # Update parent window flags
                flags = self.parent.windowFlags()
                if self.ontop_checkbox.isChecked():
                    flags |= Qt.WindowStaysOnTopHint
                else:
                    flags &= ~Qt.WindowStaysOnTopHint
                self.parent.setWindowFlags(flags)
                self.parent.show()
            
            self.accept()
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            logger.error(str(e), exc_info=True)
            self.reject()
