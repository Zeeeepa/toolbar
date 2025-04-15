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
        interval_layout.addWidget(QLabel("Check for updates every"))
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setMinimum(1)
        self.interval_spinbox.setMaximum(60)
        self.interval_spinbox.setValue(5)
        self.interval_spinbox.setSuffix(" minutes")
        interval_layout.addWidget(self.interval_spinbox)
        interval_layout.addStretch()
        notification_layout.addLayout(interval_layout)
        
        general_layout.addWidget(notification_group)
        general_layout.addStretch()
        
        # Add tabs
        tab_widget.addTab(general_tab, "General")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def load_settings(self):
        """Load current settings into the dialog."""
        if not self.config:
            return
        
        # Load token
        self.token_input.setText(self.github_monitor.token or "")
        
        # Load notification settings
        self.pr_checkbox.setChecked(self.github_monitor.notify_prs)
        self.branch_checkbox.setChecked(self.github_monitor.notify_branches)
        
        # Load monitoring interval
        self.interval_spinbox.setValue(self.github_monitor.monitor_interval // 60)
    
    def save_settings(self):
        """Save settings from the dialog."""
        if not self.config:
            QMessageBox.warning(self, "Error", "Configuration not available")
            return
        
        try:
            # Save token
            token = self.token_input.text().strip()
            self.config.set('github', 'token', token)
            
            # Save notification settings
            self.config.set('github', 'notify_prs', self.pr_checkbox.isChecked())
            self.config.set('github', 'notify_branches', self.branch_checkbox.isChecked())
            
            # Save monitoring interval
            interval_minutes = self.interval_spinbox.value()
            self.config.set('github', 'monitor_interval', interval_minutes * 60)
            
            # Save config
            self.config.save()
            
            # Update monitor
            self.github_monitor.token = token
            self.github_monitor.notify_prs = self.pr_checkbox.isChecked()
            self.github_monitor.notify_branches = self.branch_checkbox.isChecked()
            self.github_monitor.monitor_interval = interval_minutes * 60
            
            # Restart monitoring if token is valid
            if token:
                self.github_monitor.stop_monitoring()
                self.github_monitor.github = None
                
                # Reinitialize GitHub client
                from github import Github
                self.github_monitor.github = Github(token)
                
                # Start monitoring
                self.github_monitor.start_monitoring()
            else:
                self.github_monitor.stop_monitoring()
            
            QMessageBox.information(self, "Success", "Settings saved successfully")
            self.accept()
        
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save settings: {e}")
    
    def _validate_credentials(self):
        """Validate GitHub credentials."""
        token = self.token_input.text().strip()
        if not token:
            self.token_status.setText("No token provided")
            self.token_status.setStyleSheet("color: gray;")
            return
        
        try:
            # Update token in monitor temporarily
            from github import Github
            github = Github(token)
            
            # Try to get user
            user = github.get_user()
            username = user.login
            
            # Success
            self.token_status.setText(f"Authenticated as {username}")
            self.token_status.setStyleSheet("color: green;")
        
        except Exception as e:
            logger.error(f"Failed to validate GitHub token: {e}")
            self.token_status.setText(f"Authentication failed: {str(e)}")
            self.token_status.setStyleSheet("color: red;")
