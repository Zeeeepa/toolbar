"""
GitHub Settings Dialog module.
This module provides the settings dialog for the GitHub plugin.
"""

import os
import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QFormLayout, QCheckBox,
                           QSpinBox, QTabWidget, QWidget, QMessageBox,
                           QSizePolicy, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QIcon

logger = logging.getLogger(__name__)

class GitHubSettingsDialog(QDialog):
    """
    Dialog for configuring GitHub settings.
    """
    def __init__(self, github_monitor, parent=None):
        """
        Initialize the GitHub settings dialog.
        
        Args:
            github_monitor (GitHubMonitor): The GitHub monitor instance
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.github_monitor = github_monitor
        self.config = github_monitor.config if github_monitor else None
        self.setWindowTitle("GitHub Settings")
        self.setMinimumSize(500, 400)
        
        # Automatically test credentials when dialog is opened
        QTimer.singleShot(500, self._validate_credentials)
        
        # Set up the UI
        self._init_ui()
        
        # Load current settings
        self.load_settings()
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Create tabs
        tab_widget = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # API Token group
        token_group = QGroupBox("GitHub API Token")
        token_layout = QVBoxLayout(token_group)
        
        # Token input
        token_form = QFormLayout()
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText("Enter your GitHub API token")
        token_form.addRow("API Token:", self.token_input)
        token_layout.addLayout(token_form)
        
        # Token status
        self.token_status = QLabel("Not validated")
        self.token_status.setStyleSheet("color: gray;")
        token_layout.addWidget(self.token_status)
        
        # Validate button
        validate_button = QPushButton("Validate Token")
        validate_button.clicked.connect(self._validate_credentials)
        token_layout.addWidget(validate_button)
        
        # Token help text
        help_text = QLabel(
            "To create a GitHub API token, go to "
            "<a href='https://github.com/settings/tokens'>GitHub Token Settings</a> "
            "and create a new token with the 'repo' scope."
        )
        help_text.setOpenExternalLinks(True)
        help_text.setWordWrap(True)
        token_layout.addWidget(help_text)
        
        general_layout.addWidget(token_group)
        
        # Notification settings group
        notification_group = QGroupBox("Notification Settings")
        notification_layout = QVBoxLayout(notification_group)
        
        # PR notifications
        self.pr_checkbox = QCheckBox("Notify for new Pull Requests")
        notification_layout.addWidget(self.pr_checkbox)
        
        # Branch notifications
        self.branch_checkbox = QCheckBox("Notify for new Branches")
        notification_layout.addWidget(self.branch_checkbox)
        
        # Monitoring interval
        interval_layout = QHBoxLayout()
        interval_label = QLabel("Check for updates every:")
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setMinimum(1)
        self.interval_spinbox.setMaximum(3600)
        self.interval_spinbox.setValue(300)  # Default: 5 minutes
        self.interval_spinbox.setSuffix(" seconds")
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spinbox)
        interval_layout.addStretch()
        
        notification_layout.addLayout(interval_layout)
        
        general_layout.addWidget(notification_group)
        general_layout.addStretch()
        
        tab_widget.addTab(general_tab, "General")
        
        # Add tabs to layout
        layout.addWidget(tab_widget)
        
        # Buttons at the bottom
        button_layout = QHBoxLayout()
        
        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def load_settings(self):
        """Load current settings from configuration."""
        if not self.config:
            return
        
        # Load token
        token = self.config.get('github', 'token', '')
        self.token_input.setText(token)
        
        # Load notification settings
        notify_prs = self.config.get('github', 'notify_prs', True)
        notify_branches = self.config.get('github', 'notify_branches', True)
        
        self.pr_checkbox.setChecked(notify_prs)
        self.branch_checkbox.setChecked(notify_branches)
        
        # Load monitoring interval
        interval = self.config.get('github', 'monitor_interval', 300)
        self.interval_spinbox.setValue(interval)
    
    def save_settings(self):
        """Save settings to configuration."""
        if not self.config:
            QMessageBox.warning(self, "Error", "Configuration not available")
            return
        
        # Save token
        token = self.token_input.text().strip()
        self.config.set('github', 'token', token)
        
        # Save notification settings
        notify_prs = self.pr_checkbox.isChecked()
        notify_branches = self.branch_checkbox.isChecked()
        
        self.config.set('github', 'notify_prs', notify_prs)
        self.config.set('github', 'notify_branches', notify_branches)
        
        # Save monitoring interval
        interval = self.interval_spinbox.value()
        self.config.set('github', 'monitor_interval', interval)
        
        # Save configuration
        try:
            self.config.save()
            QMessageBox.information(self, "Success", "Settings saved successfully")
            
            # Update GitHub monitor
            if self.github_monitor:
                self.github_monitor.token = token
                self.github_monitor.notify_prs = notify_prs
                self.github_monitor.notify_branches = notify_branches
                self.github_monitor.monitor_interval = interval
            
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save settings: {e}")
    
    def _validate_credentials(self):
        """Validate GitHub credentials."""
        token = self.token_input.text().strip()
        
        if not token:
            self.token_status.setText("No token provided")
            self.token_status.setStyleSheet("color: gray;")
            return
        
        # Update status
        self.token_status.setText("Validating...")
        self.token_status.setStyleSheet("color: blue;")
        
        # Validate token
        if self.github_monitor:
            # Save token temporarily
            old_token = self.github_monitor.token
            self.github_monitor.token = token
            
            # Validate
            valid, username = self.github_monitor.validate_credentials()
            
            # Restore token
            self.github_monitor.token = old_token
            
            # Update status
            if valid:
                self.token_status.setText(f"Valid (User: {username})")
                self.token_status.setStyleSheet("color: green;")
            else:
                self.token_status.setText("Invalid token")
                self.token_status.setStyleSheet("color: red;")
        else:
            self.token_status.setText("Cannot validate (no monitor)")
            self.token_status.setStyleSheet("color: red;")
