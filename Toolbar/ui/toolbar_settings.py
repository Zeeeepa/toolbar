#!/usr/bin/env python3
import os
import sys
import logging
from typing import Any, Dict, List, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QSpinBox, QWidget
)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """Dialog for toolbar settings."""

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.parent = parent
        self.config = parent.config if parent else None
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the dialog UI."""
        try:
            self.setWindowTitle("Toolbar Settings")
            layout = QVBoxLayout()

            # Add settings sections
            self._add_general_settings(layout)
            self._add_appearance_settings(layout)
            self._add_notification_settings(layout)

            # Add buttons
            button_layout = QHBoxLayout()
            save_button = QPushButton("Save")
            save_button.clicked.connect(self.save_settings)
            button_layout.addWidget(save_button)

            cancel_button = QPushButton("Cancel")
            cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(cancel_button)

            layout.addLayout(button_layout)
            self.setLayout(layout)

        except Exception as e:
            logger.error("Error initializing settings dialog: %s", str(e))
            logger.error(str(e), exc_info=True)

    def _add_general_settings(self, layout: QVBoxLayout) -> None:
        """Add general settings section."""
        try:
            # General settings group
            general_group = QWidget()
            general_layout = QVBoxLayout(general_group)

            # Auto-start setting
            autostart = QCheckBox("Start with system")
            autostart.setChecked(self._get_config("autostart", False))
            general_layout.addWidget(autostart)
            self.autostart = autostart

            # Always on top setting
            always_on_top = QCheckBox("Always on top")
            always_on_top.setChecked(self._get_config("always_on_top", True))
            general_layout.addWidget(always_on_top)
            self.always_on_top = always_on_top

            layout.addWidget(general_group)

        except Exception as e:
            logger.error("Error adding general settings: %s", str(e))
            logger.error(str(e), exc_info=True)

    def _add_appearance_settings(self, layout: QVBoxLayout) -> None:
        """Add appearance settings section."""
        try:
            # Appearance settings group
            appearance_group = QWidget()
            appearance_layout = QVBoxLayout(appearance_group)

            # Opacity setting
            opacity_layout = QHBoxLayout()
            opacity_label = QLabel("Opacity:")
            opacity_layout.addWidget(opacity_label)

            opacity = QSpinBox()
            opacity.setRange(50, 100)
            opacity.setValue(int(self._get_config("opacity", 100)))
            opacity_layout.addWidget(opacity)
            self.opacity = opacity

            appearance_layout.addLayout(opacity_layout)

            # Height setting
            height_layout = QHBoxLayout()
            height_label = QLabel("Height:")
            height_layout.addWidget(height_label)

            height = QSpinBox()
            height.setRange(30, 100)
            height.setValue(int(self._get_config("height", 40)))
            height_layout.addWidget(height)
            self.height = height

            appearance_layout.addLayout(height_layout)

            layout.addWidget(appearance_group)

        except Exception as e:
            logger.error("Error adding appearance settings: %s", str(e))
            logger.error(str(e), exc_info=True)

    def _add_notification_settings(self, layout: QVBoxLayout) -> None:
        """Add notification settings section."""
        try:
            # Notification settings group
            notification_group = QWidget()
            notification_layout = QVBoxLayout(notification_group)

            # Enable notifications setting
            notifications = QCheckBox("Enable notifications")
            notifications.setChecked(self._get_config("notifications", True))
            notification_layout.addWidget(notifications)
            self.notifications = notifications

            # Notification duration setting
            duration_layout = QHBoxLayout()
            duration_label = QLabel("Duration (seconds):")
            duration_layout.addWidget(duration_label)

            duration = QSpinBox()
            duration.setRange(1, 10)
            duration.setValue(int(self._get_config("notification_duration", 3)))
            duration_layout.addWidget(duration)
            self.notification_duration = duration

            notification_layout.addLayout(duration_layout)

            layout.addWidget(notification_group)

        except Exception as e:
            logger.error("Error adding notification settings: %s", str(e))
            logger.error(str(e), exc_info=True)

    def _get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        if self.config and hasattr(self.config, key):
            return getattr(self.config, key)
        return default

    def _set_config(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        if self.config:
            setattr(self.config, key, value)

    def save_settings(self) -> None:
        """Save the settings."""
        try:
            # Save general settings
            self._set_config("autostart", self.autostart.isChecked())
            self._set_config("always_on_top", self.always_on_top.isChecked())

            # Save appearance settings
            self._set_config("opacity", self.opacity.value())
            self._set_config("height", self.height.value())

            # Save notification settings
            self._set_config("notifications", self.notifications.isChecked())
            self._set_config("notification_duration", self.notification_duration.value())

            # Save configuration
            if self.config:
                self.config.save()

            # Update parent window
            if self.parent:
                self.parent.position_toolbar()

            self.accept()

        except Exception as e:
            logger.error("Error saving settings: %s", str(e))
            logger.error(str(e), exc_info=True)
