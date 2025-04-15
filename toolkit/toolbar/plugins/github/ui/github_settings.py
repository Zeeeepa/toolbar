import os
import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QFormLayout, QCheckBox,
                           QTabWidget, QWidget, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSlot

# Configure logging
logger = logging.getLogger(__name__)

class GitHubSettingsDialog(QDialog):
    """
    Dialog for configuring GitHub settings.
    """
    def __init__(self, github_monitor, parent=None):
        """
        Initialize the GitHub settings dialog.
        
        Args:
            github_monitor: The GitHub monitor instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.github_monitor = github_monitor
        self.setWindowTitle("GitHub Settings")
        self.setMinimumSize(500, 400)
        
        # Set up the UI
        self._init_ui()
        
        # Load current settings
        self.load_settings()
        
        # Automatically test credentials when dialog is opened
        self._validate_credentials()
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        
        # Create tabs
        tab_widget = QTabWidget()
        
        # Credentials tab
        credentials_tab = QWidget()
        tab_widget.addTab(credentials_tab, "Credentials")
        
        # Notifications tab
        notifications_tab = QWidget()
        tab_widget.addTab(notifications_tab, "Notifications")
        
        # Set up credentials tab
        self._setup_credentials_tab(credentials_tab)
        
        # Set up notifications tab
        self._setup_notifications_tab(notifications_tab)
        
        layout.addWidget(tab_widget)
        
        # Buttons at the bottom
        button_layout = QHBoxLayout()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _setup_credentials_tab(self, tab):
        """Set up the credentials tab."""
        layout = QVBoxLayout(tab)
        
        # Add explanation
        explanation = QLabel(
            "GitHub authentication is required to access repository information. "
            "You can provide your GitHub username and a personal access token here. "
            "If you don't have a token, you can create one at "
            "GitHub Settings > Developer Settings > Personal Access Tokens."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        
        # Create a warning about permissions
        permissions_label = QLabel(
            "<b>Required token permissions:</b> repo"
        )
        permissions_label.setStyleSheet("color: #E65100; background-color: #FFF3E0; padding: 8px; border-radius: 4px;")
        permissions_label.setWordWrap(True)
        layout.addWidget(permissions_label)
        
        # Add username input
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        
        # Add token input
        token_layout = QHBoxLayout()
        token_label = QLabel("Token:")
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        
        token_layout.addWidget(token_label)
        token_layout.addWidget(self.token_input)
        
        # Add toggle to show/hide token
        self.show_token_checkbox = QCheckBox("Show token")
        self.show_token_checkbox.toggled.connect(self._toggle_token_visibility)
        
        # Add validation button
        validate_button = QPushButton("Validate")
        validate_button.clicked.connect(self._validate_credentials)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_credentials)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(validate_button)
        buttons_layout.addWidget(save_button)
        
        # Add credentials status indicator
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        
        # Check if credentials are loaded from env
        if os.getenv('GITHUB_TOKEN'):
            env_label = QLabel("ℹ️ GitHub token is set via environment variable.")
            env_label.setStyleSheet("color: #01579B; background-color: #E1F5FE; padding: 8px; border-radius: 4px;")
            layout.addWidget(env_label)
            
            # Add notice that saving here will override the env variable in the current session
            override_notice = QLabel(
                "Note: Saving credentials here will override the environment variable for the current session."
            )
            override_notice.setStyleSheet("color: #616161; font-style: italic;")
            override_notice.setWordWrap(True)
            layout.addWidget(override_notice)
        
        # Add everything to the layout
        layout.addLayout(username_layout)
        layout.addLayout(token_layout)
        layout.addWidget(self.show_token_checkbox)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.status_label)
        layout.addStretch()
    
    def _setup_notifications_tab(self, tab):
        """Set up the notifications tab."""
        layout = QVBoxLayout(tab)
        
        # Add explanation
        explanation = QLabel(
            "Configure how GitHub notifications are displayed in the taskbar. "
            "You can choose which types of notifications to show for all repositories."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        
        # Global notification settings
        global_settings_group = QGroupBox("Global Notification Settings")
        global_settings_layout = QVBoxLayout()
        
        # PR notifications
        self.global_pr_checkbox = QCheckBox("Show Pull Request notifications")
        self.global_pr_checkbox.setChecked(True)
        global_settings_layout.addWidget(self.global_pr_checkbox)
        
        # Branch notifications
        self.global_branch_checkbox = QCheckBox("Show Branch notifications")
        self.global_branch_checkbox.setChecked(True)
        global_settings_layout.addWidget(self.global_branch_checkbox)
        
        # Notification area
        self.notification_area_checkbox = QCheckBox("Show notification area in taskbar")
        self.notification_area_checkbox.setChecked(True)
        global_settings_layout.addWidget(self.notification_area_checkbox)
        
        global_settings_group.setLayout(global_settings_layout)
        layout.addWidget(global_settings_group)
        
        # Save button
        save_button = QPushButton("Save Notification Settings")
        save_button.clicked.connect(self.save_notification_settings)
        layout.addWidget(save_button)
        
        # Add clear notifications button
        clear_button = QPushButton("Clear All Notifications")
        clear_button.clicked.connect(self.clear_all_notifications)
        layout.addWidget(clear_button)
        
        layout.addStretch()
    
    def load_settings(self):
        """Load current settings from the GitHub monitor."""
        # Load credentials
        self.username_input.setText(self.github_monitor.username)
        self.token_input.setText(self.github_monitor.api_token)
        
        # Load notification settings
        show_pr = self.github_monitor.config.get('github', 'show_pr_notifications', True)
        show_branch = self.github_monitor.config.get('github', 'show_branch_notifications', True)
        show_area = self.github_monitor.config.get('github', 'show_notification_area', True)
        
        self.global_pr_checkbox.setChecked(show_pr)
        self.global_branch_checkbox.setChecked(show_branch)
        self.notification_area_checkbox.setChecked(show_area)
    
    def save_credentials(self):
        """Save GitHub credentials."""
        username = self.username_input.text().strip()
        token = self.token_input.text().strip()
        
        if not username or not token:
            QMessageBox.warning(self, "Error", "Username and token are required.")
            return
        
        # Set credentials in the GitHub monitor
        success = self.github_monitor.set_credentials(username, token)
        
        if success:
            QMessageBox.information(self, "Success", "GitHub credentials saved successfully.")
        else:
            QMessageBox.warning(self, "Error", "Failed to validate GitHub credentials.")
        
        # Test the credentials
        self._validate_credentials()
    
    def save_notification_settings(self):
        """Save notification settings."""
        show_pr = self.global_pr_checkbox.isChecked()
        show_branch = self.global_branch_checkbox.isChecked()
        show_area = self.notification_area_checkbox.isChecked()
        
        # Save to config
        self.github_monitor.config.set('github', 'show_pr_notifications', show_pr)
        self.github_monitor.config.set('github', 'show_branch_notifications', show_branch)
        self.github_monitor.config.set('github', 'show_notification_area', show_area)
        self.github_monitor.config.save()
        
        QMessageBox.information(self, "Success", "Notification settings saved successfully.")
    
    def clear_all_notifications(self):
        """Clear all GitHub notifications."""
        reply = QMessageBox.question(
            self, 
            "Clear Notifications", 
            "Are you sure you want to clear all GitHub notifications?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.github_monitor.clear_all_notifications()
            QMessageBox.information(self, "Success", "All notifications cleared successfully.")
    
    def _toggle_token_visibility(self, checked):
        """Toggle visibility of the token input."""
        if checked:
            self.token_input.setEchoMode(QLineEdit.Normal)
        else:
            self.token_input.setEchoMode(QLineEdit.Password)
    
    def _validate_credentials(self):
        """Validate GitHub credentials."""
        username = self.username_input.text().strip()
        token = self.token_input.text().strip()
        
        # If no credentials in the fields, check environment variables
        if not username or not token:
            username = os.getenv('GITHUB_USERNAME', '')
            token = os.getenv('GITHUB_TOKEN', '')
            if username and token:
                self.status_label.setText("ℹ️ Using credentials from environment variables")
                self.status_label.setStyleSheet("color: #01579B;")
                return
            else:
                self.status_label.setText("❌ No credentials found. Please enter your GitHub username and token.")
                self.status_label.setStyleSheet("color: #B71C1C;")
                return
        
        try:
            # Test the credentials by making a GitHub API request
            import requests
            response = requests.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.status_label.setText(f"✅ Valid credentials! Logged in as {user_data.get('login')}.")
                self.status_label.setStyleSheet("color: #2E7D32;")
            else:
                error_message = response.json().get('message', 'Unknown error')
                self.status_label.setText(f"❌ Authentication failed: {response.status_code} - {error_message}")
                self.status_label.setStyleSheet("color: #B71C1C;")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("color: #B71C1C;")
            logger.error(f"Error validating GitHub credentials: {e}")
