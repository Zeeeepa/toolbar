#!/usr/bin/env python3
import os
import sys
import logging
from typing import Dict, List, Any, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QSpinBox, QLineEdit
)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """Settings dialog for toolbar configuration"""
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        """Initialize dialog UI"""
        try:
            self.setWindowTitle("Toolbar Settings")
            layout = QVBoxLayout()

            # Add settings controls
            self.add_general_settings(layout)
            self.add_plugin_settings(layout)
            self.add_notification_settings(layout)

            # Add buttons
            button_layout = QHBoxLayout()
            save_button = QPushButton("Save")
            save_button.clicked.connect(self.save_settings)
            cancel_button = QPushButton("Cancel")
            cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(save_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)

            self.setLayout(layout)

        except Exception as e:
            logger.error("Error initializing settings dialog: %s", str(e))
            logger.error(str(e), exc_info=True)

    def add_general_settings(self, layout):
        """Add general settings section"""
        try:
            # Add section label
            layout.addWidget(QLabel("<b>General Settings</b>"))

            # Add startup checkbox
            self.startup_checkbox = QCheckBox("Start with Windows")
            self.startup_checkbox.setChecked(getattr(self.config, "start_with_windows", False))
            layout.addWidget(self.startup_checkbox)

            # Add position settings
            position_layout = QHBoxLayout()
            position_layout.addWidget(QLabel("Screen Position:"))
            self.position_spinbox = QSpinBox()
            self.position_spinbox.setRange(0, 100)
            self.position_spinbox.setValue(getattr(self.config, "screen_position", 0))
            position_layout.addWidget(self.position_spinbox)
            layout.addLayout(position_layout)

        except Exception as e:
            logger.error("Error adding general settings: %s", str(e))
            logger.error(str(e), exc_info=True)

    def add_plugin_settings(self, layout):
        """Add plugin settings section"""
        try:
            # Add section label
            layout.addWidget(QLabel("<b>Plugin Settings</b>"))

            # Add plugin directory
            plugin_layout = QHBoxLayout()
            plugin_layout.addWidget(QLabel("Plugin Directory:"))
            self.plugin_dir_edit = QLineEdit()
            self.plugin_dir_edit.setText(getattr(self.config, "plugin_dir", ""))
            plugin_layout.addWidget(self.plugin_dir_edit)
            layout.addLayout(plugin_layout)

        except Exception as e:
            logger.error("Error adding plugin settings: %s", str(e))
            logger.error(str(e), exc_info=True)

    def add_notification_settings(self, layout):
        """Add notification settings section"""
        try:
            # Add section label
            layout.addWidget(QLabel("<b>Notification Settings</b>"))

            # Add notification checkbox
            self.notification_checkbox = QCheckBox("Enable Notifications")
            self.notification_checkbox.setChecked(getattr(self.config, "notifications_enabled", True))
            layout.addWidget(self.notification_checkbox)

            # Add notification duration
            duration_layout = QHBoxLayout()
            duration_layout.addWidget(QLabel("Notification Duration (seconds):"))
            self.duration_spinbox = QSpinBox()
            self.duration_spinbox.setRange(1, 60)
            self.duration_spinbox.setValue(getattr(self.config, "notification_duration", 5))
            duration_layout.addWidget(self.duration_spinbox)
            layout.addLayout(duration_layout)

        except Exception as e:
            logger.error("Error adding notification settings: %s", str(e))
            logger.error(str(e), exc_info=True)

    def save_settings(self):
        """Save settings to configuration"""
        try:
            # Save general settings
            self.config.start_with_windows = self.startup_checkbox.isChecked()
            self.config.screen_position = self.position_spinbox.value()

            # Save plugin settings
            self.config.plugin_dir = self.plugin_dir_edit.text()

            # Save notification settings
            self.config.notifications_enabled = self.notification_checkbox.isChecked()
            self.config.notification_duration = self.duration_spinbox.value()

            # Save configuration
            self.config.save()
            self.accept()

        except Exception as e:
            logger.error("Error saving settings: %s", str(e))
            logger.error(str(e), exc_info=True)
