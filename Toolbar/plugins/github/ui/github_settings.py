import warnings
import os
import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QFormLayout, QCheckBox,
                            QSpinBox, QTabWidget, QWidget, QMessageBox,
                            QSizePolicy, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QIcon

# Suppress PyQt5 deprecation warnings
warnings.filterwarnings("ignore", message=".*sipPyTypeDict.*")

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
        self.setMinimumSize(500, 450)
        
        # Automatically test credentials when dialog is opened
        QTimer.singleShot(500, self._validate_credentials)
        
        # Set up the UI
        self._init_ui()
        
        # Apply dark theme
        self.apply_dark_theme()
        
        # Load current settings
        self.load_settings()
        
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        
        # Create tabs
        tab_widget = QTabWidget()
        
        # Credentials tab
        credentials_tab = QWidget()
        tab_widget.addTab(credentials_tab, "Credentials")
        
        # Webhook tab
        webhook_tab = QWidget()
        tab_widget.addTab(webhook_tab, "Webhooks")
        
        # Projects tab
        projects_tab = QWidget()
        tab_widget.addTab(projects_tab, "Projects")
        
        # Set up credentials tab
        self._setup_credentials_tab(credentials_tab)
        
        # Set up webhook tab
        self._setup_webhook_tab(webhook_tab)
        
        # Set up projects tab
        self._setup_projects_tab(projects_tab)
        
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
            "<b>Required token permissions:</b> repo, admin:repo_hook"
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
        
        # Load current credentials
        username, token = self.github_monitor.config.get_github_credentials() if self.github_monitor else ("", "")
        self.username_input.setText(username)
        self.token_input.setText(token)
    
    def _setup_webhook_tab(self, tab):
        """Set up the webhook tab."""
        layout = QVBoxLayout(tab)
        
        # Add explanation
        explanation = QLabel(
            "GitHub webhooks allow the toolbar to receive real-time notifications "
            "about repository events. To set up webhooks, you need to start a webhook "
            "server and provide an ngrok authentication token."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        
        # Add webhook status indicator
        self.webhook_status = QLabel("Webhook Server: Stopped")
        self.webhook_status.setStyleSheet("color: #616161; font-weight: bold;")
        layout.addWidget(self.webhook_status)
        
        # Add webhook URL display
        self.webhook_url_label = QLabel("Webhook URL: N/A")
        self.webhook_url_label.setWordWrap(True)
        self.webhook_url_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.webhook_url_label)
        
        # Add port selection
        port_layout = QHBoxLayout()
        port_label = QLabel("Webhook Port:")
        self.port_input = QSpinBox()
        self.port_input.setRange(1024, 65535)
        self.port_input.setValue(8000)
        
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        port_layout.addStretch()
        
        # Add ngrok token input
        token_layout = QHBoxLayout()
        token_label = QLabel("ngrok Token:")
        self.ngrok_token_input = QLineEdit()
        self.ngrok_token_input.setEchoMode(QLineEdit.Password)
        
        token_layout.addWidget(token_label)
        token_layout.addWidget(self.ngrok_token_input)
        
        # Add help text for ngrok
        ngrok_help = QLabel(
            "To use webhooks, you need an ngrok authentication token. "
            "Get your token at <a href='https://dashboard.ngrok.com/get-started/your-authtoken'>ngrok.com</a>. "
            "You'll also need to install ngrok from <a href='https://ngrok.com/download'>ngrok.com/download</a>."
        )
        ngrok_help.setWordWrap(True)
        ngrok_help.setOpenExternalLinks(True)
        ngrok_help.setStyleSheet("color: #616161; font-style: italic;")
        
        # Add webhook buttons
        self.start_webhook_button = QPushButton("Start Webhook Server")
        self.start_webhook_button.clicked.connect(self.start_webhook_server)
        
        self.stop_webhook_button = QPushButton("Stop Webhook Server")
        self.stop_webhook_button.clicked.connect(self.stop_webhook_server)
        self.stop_webhook_button.setEnabled(False)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.start_webhook_button)
        buttons_layout.addWidget(self.stop_webhook_button)
        buttons_layout.addStretch()
        
        # Add everything to the layout
        layout.addLayout(port_layout)
        layout.addLayout(token_layout)
        layout.addWidget(ngrok_help)
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        # Load current ngrok token
        ngrok_token = self.github_monitor.config.get_ngrok_auth_token() if self.github_monitor else ""
        self.ngrok_token_input.setText(ngrok_token)
        
        # Update webhook status on init
        if self.github_monitor and hasattr(self.github_monitor, 'webhook_handler') and self.github_monitor.webhook_handler and self.github_monitor.webhook_handler.running:
            self.webhook_status.setText("Webhook Server: Running")
            self.webhook_status.setStyleSheet("color: #2E7D32; font-weight: bold;")
            self.start_webhook_button.setEnabled(False)
            self.stop_webhook_button.setEnabled(True)
            
            # Set webhook URL if available
            if hasattr(self.github_monitor, 'webhook_url') and self.github_monitor.webhook_url:
                self.webhook_url_label.setText(f"Webhook URL: {self.github_monitor.webhook_url}")
    
    def _setup_projects_tab(self, tab):
        """Set up the projects tab."""
        layout = QVBoxLayout(tab)
        
        # Add explanation
        explanation = QLabel(
            "GitHub Projects allows you to pin your favorite repositories to the toolbar. "
            "Click the button below to manage your pinned projects."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        
        # Add projects button
        projects_button = QPushButton("Manage Projects")
        projects_button.clicked.connect(self.open_projects_dialog)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(projects_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addStretch()
    
    def save_credentials(self):
        """Save the GitHub credentials."""
        if not self.github_monitor:
            QMessageBox.warning(self, "Error", "GitHub monitor not initialized.")
            return
            
        username = self.username_input.text().strip()
        token = self.token_input.text().strip()
        
        # Save credentials
        self.github_monitor.config.set_github_credentials(username, token)
        
        # Update GitHub monitor
        self.github_monitor.set_credentials(username, token)
        
        # Show confirmation message
        QMessageBox.information(self, "Success", "GitHub credentials saved successfully.")
        
        # Test the credentials
        self._validate_credentials()
    
    def _toggle_token_visibility(self, checked):
        if checked:
            self.token_input.setEchoMode(QLineEdit.Normal)
        else:
            self.token_input.setEchoMode(QLineEdit.Password)
    
    def _validate_credentials(self):
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
                
                # Show more detailed error message based on status code
                if response.status_code == 401:
                    QMessageBox.warning(
                        self, 
                        "Authentication Failed", 
                        "Your GitHub token is invalid or has expired. Please check your credentials or generate a new token."
                    )
                elif response.status_code == 403:
                    QMessageBox.warning(
                        self, 
                        "Rate Limit Exceeded", 
                        "You've exceeded GitHub's rate limit. Please try again later."
                    )
        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)}")
            self.status_label.setStyleSheet("color: #B71C1C;")
            logger.error(f"Error validating GitHub credentials: {e}")
            QMessageBox.critical(self, "Error", f"Failed to validate credentials: {str(e)}")
    
    def start_webhook_server(self):
        """Start the webhook server."""
        if not self.github_monitor:
            QMessageBox.warning(self, "Error", "GitHub monitor not initialized.")
            return
        
        port = self.port_input.value()
        ngrok_token = self.ngrok_token_input.text().strip()
        
        if not ngrok_token:
            QMessageBox.warning(self, "Error", "ngrok authentication token is required.")
            return
        
        # Save ngrok token
        self.github_monitor.config.set_ngrok_auth_token(ngrok_token)
        
        try:
            # Start webhook server
            webhook_url = self.github_monitor.setup_webhook_server(port, ngrok_token)
            
            if webhook_url:
                # Update UI
                self.webhook_status.setText("Webhook Server: Running")
                self.webhook_status.setStyleSheet("color: #2E7D32; font-weight: bold;")
                self.webhook_url_label.setText(f"Webhook URL: {webhook_url}")
                
                # Update button states
                self.start_webhook_button.setEnabled(False)
                self.stop_webhook_button.setEnabled(True)
                
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Webhook server started successfully!\nWebhook URL: {webhook_url}"
                )
            else:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    "Failed to start webhook server. Please check the logs for details."
                )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error starting webhook server: {error_msg}")
            
            # Check for 401 unauthorized error
            if "401" in error_msg and "Bad credentials" in error_msg:
                QMessageBox.critical(
                    self, 
                    "GitHub Authentication Failed", 
                    "Your GitHub token is invalid or doesn't have the required permissions.\n\n"
                    "Please check your credentials in the Credentials tab and make sure your token has 'repo' and 'admin:repo_hook' scopes."
                )
            else:
                QMessageBox.critical(
                    self, 
                    "Error", 
                    f"Failed to start webhook server: {error_msg}\n\nPlease check the logs for details."
                )
    
    def stop_webhook_server(self):
        """Stop the webhook server."""
        if not self.github_monitor:
            QMessageBox.warning(self, "Error", "GitHub monitor not initialized.")
            return
        
        try:
            # Stop webhook server
            success = self.github_monitor.stop_webhook_server()
            
            if success:
                # Update UI
                self.webhook_status.setText("Webhook Server: Stopped")
                self.webhook_status.setStyleSheet("color: #616161; font-weight: bold;")
                self.webhook_url_label.setText("Webhook URL: N/A")
                
                # Update button states
                self.start_webhook_button.setEnabled(True)
                self.stop_webhook_button.setEnabled(False)
                
                QMessageBox.information(self, "Success", "Webhook server stopped successfully.")
            else:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    "Failed to stop webhook server. Please check the logs for details."
                )
        except Exception as e:
            logger.error(f"Error stopping webhook server: {e}")
            QMessageBox.critical(self, "Error", f"Failed to stop webhook server: {str(e)}")
    
    def _update_webhook_button_states(self):
        """Update webhook button states based on current webhook status."""
        if not self.github_monitor:
            self.start_webhook_button.setEnabled(False)
            self.stop_webhook_button.setEnabled(False)
            return
        
        if hasattr(self.github_monitor, 'webhook_handler') and self.github_monitor.webhook_handler and self.github_monitor.webhook_handler.running:
            self.start_webhook_button.setEnabled(False)
            self.stop_webhook_button.setEnabled(True)
        else:
            self.start_webhook_button.setEnabled(True)
            self.stop_webhook_button.setEnabled(False)
    
    def open_projects_dialog(self):
        """Open the projects dialog."""
        if not self.github_monitor:
            QMessageBox.warning(self, "Error", "GitHub monitor not initialized.")
            return
            
        from Toolbar.ui.github_project_ui import GitHubProjectsDialog
        
        dialog = GitHubProjectsDialog(self.github_monitor, self)
        dialog.exec_()

    def apply_dark_theme(self):
        """Apply a dark theme to the dialog elements."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: #e1e1e1;
            }
            QLabel {
                color: #e1e1e1;
                font-weight: bold;
            }
            QGroupBox {
                color: #e1e1e1;
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 4px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }
            QLineEdit, QTextEdit {
                background-color: #383838;
                color: #e1e1e1;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QCheckBox {
                color: #e1e1e1;
            }
            QSpinBox {
                background-color: #383838;
                color: #e1e1e1;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0086e8;
            }
            QPushButton:pressed {
                background-color: #005fa3;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #aaaaaa;
            }
        """)

    def load_settings(self):
        """Load current settings from the GitHub monitor."""
        # Implement the logic to load settings from the GitHub monitor
        pass
