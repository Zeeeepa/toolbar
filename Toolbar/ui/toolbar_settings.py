#!/usr/bin/env python3
import os
import sys
import logging
from typing import Any, Dict, List, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QSpinBox, QLineEdit
)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """Dialog for toolbar settings."""

    def __init__(self, config: Any):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the settings dialog UI."""
        try:
            # Set dialog properties
            self.setWindowTitle("Toolbar Settings")
            self.setMinimumWidth(400)

            # Create layout
            layout = QVBoxLayout()
            self.setLayout(layout)

            # Add settings sections
            self._add_general_settings(layout)
            self._add_appearance_settings(layout)
            self._add_plugin_settings(layout)

            # Add buttons
            button_layout = QHBoxLayout()
            save_button = QPushButton("Save")
            save_button.clicked.connect(self.save_settings)
            button_layout.addWidget(save_button)

            cancel_button = QPushButton("Cancel")
            cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(cancel_button)

            layout.addLayout(button_layout)

        except Exception as e:
            logger.error(f"Error initializing settings dialog: {str(e)}")
            logger.error(str(e), exc_info=True)

    def _add_general_settings(self, layout: Any) -> None:
        """Add general settings section."""
        try:
            # General settings group
            layout.addWidget(QLabel("<b>General Settings</b>"))

            # Auto-start setting
            autostart = QCheckBox("Start with system")
            autostart.setChecked(self.config.get("autostart", False))
            layout.addWidget(autostart)

            # Position setting
            position_layout = QHBoxLayout()
            position_layout.addWidget(QLabel("Screen position:"))
            position_combo = QLineEdit()
            position_combo.setText(self.config.get("position", "bottom"))
            position_layout.addWidget(position_combo)
            layout.addLayout(position_layout)

        except Exception as e:
            logger.error(f"Error adding general settings: {str(e)}")
            logger.error(str(e), exc_info=True)

    def _add_appearance_settings(self, layout: Any) -> None:
        """Add appearance settings section."""
        try:
            # Appearance settings group
            layout.addWidget(QLabel("<b>Appearance</b>"))

            # Opacity setting
            opacity_layout = QHBoxLayout()
            opacity_layout.addWidget(QLabel("Opacity:"))
            opacity_spin = QSpinBox()
            opacity_spin.setRange(50, 100)
            opacity_spin.setValue(int(self.config.get("opacity", 90)))
            opacity_layout.addWidget(opacity_spin)
            layout.addLayout(opacity_layout)

            # Theme setting
            theme_layout = QHBoxLayout()
            theme_layout.addWidget(QLabel("Theme:"))
            theme_combo = QLineEdit()
            theme_combo.setText(self.config.get("theme", "dark"))
            theme_layout.addWidget(theme_combo)
            layout.addLayout(theme_layout)

        except Exception as e:
            logger.error(f"Error adding appearance settings: {str(e)}")
            logger.error(str(e), exc_info=True)

    def _add_plugin_settings(self, layout: Any) -> None:
        """Add plugin settings section."""
        try:
            # Plugin settings group
            layout.addWidget(QLabel("<b>Plugin Settings</b>"))

            # Plugin directory setting
            plugin_dir_layout = QHBoxLayout()
            plugin_dir_layout.addWidget(QLabel("Plugin directory:"))
            plugin_dir_edit = QLineEdit()
            plugin_dir_edit.setText(self.config.get("plugin_dir", ""))
            plugin_dir_layout.addWidget(plugin_dir_edit)
            layout.addLayout(plugin_dir_layout)

        except Exception as e:
            logger.error(f"Error adding plugin settings: {str(e)}")
            logger.error(str(e), exc_info=True)

    def save_settings(self) -> None:
        """Save the settings and close the dialog."""
        try:
            # Save settings to config
            self.config.save()
            self.accept()
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            logger.error(str(e), exc_info=True)
