#!/usr/bin/env python3
import os
import sys
import logging
from typing import Dict, List, Optional, Any

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QCheckBox, QPushButton, QTabWidget, QWidget,
    QGroupBox, QFormLayout, QSpinBox, QMessageBox, QFileDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class ToolbarSettingsDialog(QDialog):
    """Settings dialog for the Toolbar application."""
    
    def __init__(self, config, parent=None):
        """
        Initialize the settings dialog.
        
        Args:
            config: Configuration object
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config
        
        # Set dialog properties
        self.setWindowTitle("Toolbar Settings")
        self.setMinimumSize(500, 400)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_general_tab()
        self._create_github_tab()
        self._create_linear_tab()
        self._create_plugins_tab()
        self._create_appearance_tab()
        
        # Create buttons
        self._create_buttons()
        
        logger.info("Settings dialog initialized")
    
    def _create_general_tab(self):
        """Create general settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create general settings group
        group = QGroupBox("General Settings")
        group_layout = QFormLayout(group)
        
        # Create auto-start checkbox
        self.auto_start_checkbox = QCheckBox("Start on system boot")
        self.auto_start_checkbox.setChecked(self.config.get_setting("auto_start", False))
        group_layout.addRow("", self.auto_start_checkbox)
        
        # Create minimize to tray checkbox
        self.minimize_to_tray_checkbox = QCheckBox("Minimize to system tray")
        self.minimize_to_tray_checkbox.setChecked(self.config.get_setting("minimize_to_tray", True))
        group_layout.addRow("", self.minimize_to_tray_checkbox)
        
        layout.addWidget(group)
        
        # Add tab
        self.tab_widget.addTab(tab, "General")
    
    def _create_github_tab(self):
        """Create GitHub settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create GitHub settings group
        group = QGroupBox("GitHub Settings")
        group_layout = QFormLayout(group)
        
        # Create token field
        self.github_token_field = QLineEdit()
        self.github_token_field.setText(self.config.get_setting("github.token", ""))
        self.github_token_field.setEchoMode(QLineEdit.Password)
        group_layout.addRow("API Token:", self.github_token_field)
        
        # Create username field
        self.github_username_field = QLineEdit()
        self.github_username_field.setText(self.config.get_setting("github.username", ""))
        group_layout.addRow("Username:", self.github_username_field)
        
        layout.addWidget(group)
        
        # Add tab
        self.tab_widget.addTab(tab, "GitHub")
    
    def _create_linear_tab(self):
        """Create Linear settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create Linear settings group
        group = QGroupBox("Linear Settings")
        group_layout = QFormLayout(group)
        
        # Create API key field
        self.linear_api_key_field = QLineEdit()
        self.linear_api_key_field.setText(self.config.get_setting("linear.api_key", ""))
        self.linear_api_key_field.setEchoMode(QLineEdit.Password)
        group_layout.addRow("API Key:", self.linear_api_key_field)
        
        # Create team ID field
        self.linear_team_id_field = QLineEdit()
        self.linear_team_id_field.setText(self.config.get_setting("linear.team_id", ""))
        group_layout.addRow("Team ID:", self.linear_team_id_field)
        
        layout.addWidget(group)
        
        # Add tab
        self.tab_widget.addTab(tab, "Linear")
    
    def _create_plugins_tab(self):
        """Create plugins settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create plugins settings group
        group = QGroupBox("Plugin Settings")
        group_layout = QVBoxLayout(group)
        
        # Create plugin checkboxes
        self.plugin_checkboxes = {}
        
        # Get enabled and disabled plugins
        enabled_plugins = self.config.get_setting("plugins.enabled", [])
        disabled_plugins = self.config.get_setting("plugins.disabled", [])
        
        # Get all plugins
        plugins = {}
        for plugin_dir in self.config.get_setting("plugins.directories", []):
            if os.path.isdir(plugin_dir):
                for item in os.listdir(plugin_dir):
                    item_path = os.path.join(plugin_dir, item)
                    if os.path.isdir(item_path) and not item.startswith("."):
                        plugins[item] = item_path
        
        # Add checkboxes for each plugin
        for name, path in plugins.items():
            checkbox = QCheckBox(name)
            checkbox.setChecked(name not in disabled_plugins)
            self.plugin_checkboxes[name] = checkbox
            group_layout.addWidget(checkbox)
        
        group_layout.addStretch()
        layout.addWidget(group)
        
        # Add tab
        self.tab_widget.addTab(tab, "Plugins")
    
    def _create_appearance_tab(self):
        """Create appearance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create appearance settings group
        group = QGroupBox("Appearance Settings")
        group_layout = QFormLayout(group)
        
        # Create theme combo box
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        theme = self.config.get_setting("ui.theme", "system")
        if theme.lower() == "light":
            self.theme_combo.setCurrentIndex(1)
        elif theme.lower() == "dark":
            self.theme_combo.setCurrentIndex(2)
        else:
            self.theme_combo.setCurrentIndex(0)
        group_layout.addRow("Theme:", self.theme_combo)
        
        # Create font size spin box
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.config.get_setting("ui.font_size", 12))
        group_layout.addRow("Font Size:", self.font_size_spin)
        
        # Create toolbar position combo box
        self.position_combo = QComboBox()
        self.position_combo.addItems(["Top", "Bottom", "Left", "Right", "Center"])
        position = self.config.get_setting("ui.toolbar_position", "top")
        if position.lower() == "bottom":
            self.position_combo.setCurrentIndex(1)
        elif position.lower() == "left":
            self.position_combo.setCurrentIndex(2)
        elif position.lower() == "right":
            self.position_combo.setCurrentIndex(3)
        elif position.lower() == "center":
            self.position_combo.setCurrentIndex(4)
        else:
            self.position_combo.setCurrentIndex(0)
        group_layout.addRow("Toolbar Position:", self.position_combo)
        
        layout.addWidget(group)
        
        # Add tab
        self.tab_widget.addTab(tab, "Appearance")
    
    def _create_buttons(self):
        """Create dialog buttons."""
        button_layout = QHBoxLayout()
        
        # Create save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self._save_settings)
        button_layout.addWidget(save_button)
        
        # Create cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        self.layout.addLayout(button_layout)
    
    def _save_settings(self):
        """Save settings."""
        try:
            # Save general settings
            self.config.set_setting("auto_start", self.auto_start_checkbox.isChecked())
            self.config.set_setting("minimize_to_tray", self.minimize_to_tray_checkbox.isChecked())
            
            # Save GitHub settings
            self.config.set_setting("github.token", self.github_token_field.text())
            self.config.set_setting("github.username", self.github_username_field.text())
            
            # Save Linear settings
            self.config.set_setting("linear.api_key", self.linear_api_key_field.text())
            self.config.set_setting("linear.team_id", self.linear_team_id_field.text())
            
            # Save plugin settings
            for name, checkbox in self.plugin_checkboxes.items():
                if checkbox.isChecked():
                    self.config.enable_plugin(name)
                else:
                    self.config.disable_plugin(name)
            
            # Save appearance settings
            theme_index = self.theme_combo.currentIndex()
            if theme_index == 1:
                self.config.set_setting("ui.theme", "light")
            elif theme_index == 2:
                self.config.set_setting("ui.theme", "dark")
            else:
                self.config.set_setting("ui.theme", "system")
            
            self.config.set_setting("ui.font_size", self.font_size_spin.value())
            
            position_index = self.position_combo.currentIndex()
            if position_index == 1:
                self.config.set_setting("ui.toolbar_position", "bottom")
            elif position_index == 2:
                self.config.set_setting("ui.toolbar_position", "left")
            elif position_index == 3:
                self.config.set_setting("ui.toolbar_position", "right")
            elif position_index == 4:
                self.config.set_setting("ui.toolbar_position", "center")
            else:
                self.config.set_setting("ui.toolbar_position", "top")
            
            # Save configuration
            self.config.save()
            
            logger.info("Settings saved")
            
            # Close dialog
            self.accept()
        except Exception as e:
            logger.error(f"Error saving settings: {e}", exc_info=True)
            QMessageBox.critical(self, "Save Error", f"Error saving settings: {str(e)}")
