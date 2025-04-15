import warnings
import webbrowser
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QToolButton, QMenu, QAction, QTabWidget, QDialog, QMessageBox,
                            QCheckBox, QGroupBox, QFormLayout, QLineEdit, QComboBox, QListWidget, QListWidgetItem)
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import Qt, pyqtSignal

import os
import json
import logging
from datetime import datetime

# Import from local modules
from Toolbar.plugins.github.ui.github_settings import GitHubSettingsDialog
from Toolbar.plugins.github.ui.github_project_ui import GitHubProjectsDialog
from Toolbar.plugins.github.ui.project_icon_ui import ProjectIconWidget

# Configure logging
logger = logging.getLogger(__name__)

class NotificationWidget(QWidget):
    """
    Widget for displaying a GitHub notification.
    """
    
    def __init__(self, notification, parent=None):
        """
        Initialize the notification widget.
        
        Args:
            notification: The notification to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.notification = notification
        self.parent_ui = parent
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Icon based on notification type
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "icons", f"{self.notification.type}.svg")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                    "icons", "notification.svg")
        
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(icon_path).pixmap(16, 16))
        layout.addWidget(icon_label)
        
        # Notification text
        text_label = QLabel(self.notification.message)
        text_label.setWordWrap(True)
        layout.addWidget(text_label, 1)
        
        # Time
        time_str = self.notification.timestamp.strftime("%H:%M")
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: gray;")
        layout.addWidget(time_label)
        
        # Open button
        open_button = QPushButton("Open")
        open_button.setToolTip("Open in browser")
        open_button.clicked.connect(self.open_notification)
        layout.addWidget(open_button)
        
        # Close button
        close_button = QPushButton("×")
        close_button.setToolTip("Dismiss notification")
        close_button.setMaximumWidth(20)
        close_button.clicked.connect(self.remove_notification)
        layout.addWidget(close_button)
        
        # Set background color
        self.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        
    def open_notification(self):
        """Open the notification URL in a browser."""
        try:
            webbrowser.open(self.notification.url)
        except Exception as e:
            warnings.warn(f"Failed to open notification URL: {e}")
            
    def remove_notification(self):
        """Remove the notification."""
        try:
            if self.parent_ui and hasattr(self.parent_ui, 'remove_notification'):
                self.parent_ui.remove_notification(self)
        except Exception as e:
            warnings.warn(f"Failed to remove notification: {e}")

class GitHubUI(QWidget):
    """
    Main UI for GitHub integration.
    """
    
    def __init__(self, github_monitor, parent=None):
        """
        Initialize the GitHub UI.
        
        Args:
            github_monitor: The GitHub monitor instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.github_monitor = github_monitor
        self.parent = parent
        
        # Connect signals
        self.github_monitor.notification_received.connect(self.add_notification)
        self.github_monitor.project_notification_received.connect(self.add_project_notification)
        
        self.init_ui()
        self.load_pinned_projects()
        
    def init_ui(self):
        """Initialize the UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a tabbed interface for the settings dialog
        self.tabs = QTabWidget()
        
        # GitHub icon button (will be positioned on the left side of the toolbar)
        self.github_button = QToolButton()
        self.github_button.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                "icons", "github.svg")))
        self.github_button.setToolTip("GitHub")
        self.github_button.clicked.connect(self.show_github_dialog)
        
        # Toolbar for GitHub actions
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(toolbar_layout)
        
        # Projects container
        projects_container = QWidget()
        self.projects_layout = QHBoxLayout(projects_container)
        self.projects_layout.setContentsMargins(0, 0, 0, 0)
        self.projects_layout.setSpacing(5)
        main_layout.addWidget(projects_container)
        
        # Notifications container
        notifications_container = QWidget()
        self.notifications_layout = QVBoxLayout(notifications_container)
        self.notifications_layout.setContentsMargins(10, 10, 10, 10)
        self.notifications_layout.setSpacing(5)
        main_layout.addWidget(notifications_container)
        
        # Add stretch to push everything to the top
        main_layout.addStretch(1)
        
        # Initialize collections
        self.notification_widgets = []
        self.project_widgets = {}
        
        # Create notification badge for the toolbar
        self.notification_badge = QLabel("0")
        self.notification_badge.setStyleSheet("background-color: red; color: white; border-radius: 10px; padding: 2px;")
        self.notification_badge.setAlignment(Qt.AlignCenter)
        self.notification_badge.setVisible(False)
    
    def show_github_dialog(self):
        """Show GitHub settings dialog with tabs."""
        dialog = QDialog(self)
        dialog.setWindowTitle("GitHub")
        dialog.setMinimumSize(800, 600)
        
        # Create layout
        layout = QVBoxLayout(dialog)
        
        # Create tabs
        tabs = QTabWidget()
        
        # API tab
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)
        api_settings = GitHubSettingsDialog(self.github_monitor, dialog)
        api_layout.addWidget(api_settings)
        tabs.addTab(api_tab, "API")
        
        # Projects tab
        projects_tab = QWidget()
        projects_layout = QVBoxLayout(projects_tab)
        projects_dialog = GitHubProjectsDialog(self.github_monitor, dialog)
        projects_layout.addWidget(projects_dialog)
        tabs.addTab(projects_tab, "Projects")
        
        # Monitoring tab
        monitoring_tab = QWidget()
        monitoring_layout = QVBoxLayout(monitoring_tab)
        
        # Add monitoring options
        monitoring_label = QLabel("Notification Settings")
        monitoring_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        monitoring_layout.addWidget(monitoring_label)
        
        # PR notifications checkbox
        self.pr_notifications_checkbox = QCheckBox("Notify on new Pull Requests")
        self.pr_notifications_checkbox.setChecked(self.github_monitor.get_setting("notify_pr", True))
        monitoring_layout.addWidget(self.pr_notifications_checkbox)
        
        # Branch notifications checkbox
        self.branch_notifications_checkbox = QCheckBox("Notify on new Branches")
        self.branch_notifications_checkbox.setChecked(self.github_monitor.get_setting("notify_branch", True))
        monitoring_layout.addWidget(self.branch_notifications_checkbox)
        
        # Notification display options
        notification_display_group = QGroupBox("Notification Display")
        notification_display_layout = QVBoxLayout(notification_display_group)
        
        # Show notification badge checkbox
        self.show_badge_checkbox = QCheckBox("Show notification badge on GitHub icon")
        self.show_badge_checkbox.setChecked(self.github_monitor.get_setting("show_badge", True))
        notification_display_layout.addWidget(self.show_badge_checkbox)
        
        # Show project badges checkbox
        self.show_project_badges_checkbox = QCheckBox("Show notification badges on project icons")
        self.show_project_badges_checkbox.setChecked(self.github_monitor.get_setting("show_project_badges", True))
        notification_display_layout.addWidget(self.show_project_badges_checkbox)
        
        # Add notification display group to monitoring layout
        monitoring_layout.addWidget(notification_display_group)
        
        # Save monitoring settings button
        save_monitoring_button = QPushButton("Save Notification Settings")
        save_monitoring_button.clicked.connect(self.save_monitoring_settings)
        monitoring_layout.addWidget(save_monitoring_button)
        
        monitoring_layout.addStretch()
        tabs.addTab(monitoring_tab, "Monitoring")
        
        # PR & Branch Settings tab
        pr_settings_tab = QWidget()
        pr_settings_layout = QVBoxLayout(pr_settings_tab)
        
        # Add PR & Branch settings
        pr_settings_label = QLabel("PR & Branch Settings")
        pr_settings_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        pr_settings_layout.addWidget(pr_settings_label)
        
        # Auto-merge rules
        auto_merge_group = QGroupBox("Auto-merge Rules")
        auto_merge_layout = QVBoxLayout(auto_merge_group)
        
        # Auto-merge markdown and prompt files
        self.auto_merge_md_prompt_checkbox = QCheckBox("Auto-merge when only .md and .prompt files are changed")
        self.auto_merge_md_prompt_checkbox.setChecked(self.github_monitor.get_setting("auto_merge_md_prompt", False))
        auto_merge_layout.addWidget(self.auto_merge_md_prompt_checkbox)
        
        # Add auto-merge group to PR settings layout
        pr_settings_layout.addWidget(auto_merge_group)
        
        # Save PR settings button
        save_pr_settings_button = QPushButton("Save PR Settings")
        save_pr_settings_button.clicked.connect(self.save_pr_settings)
        pr_settings_layout.addWidget(save_pr_settings_button)
        
        pr_settings_layout.addStretch()
        tabs.addTab(pr_settings_tab, "PR & Branch Settings")
        
        # Add tabs to layout
        layout.addWidget(tabs)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        # Show dialog
        dialog.exec_()
        
        # Reload pinned projects after dialog is closed
        self.load_pinned_projects()
    
    def save_monitoring_settings(self):
        """Save monitoring settings."""
        try:
            # Save notification settings
            self.github_monitor.set_setting("notify_pr", self.pr_notifications_checkbox.isChecked())
            self.github_monitor.set_setting("notify_branch", self.branch_notifications_checkbox.isChecked())
            self.github_monitor.set_setting("show_badge", self.show_badge_checkbox.isChecked())
            self.github_monitor.set_setting("show_project_badges", self.show_project_badges_checkbox.isChecked())
            self.github_monitor.config.save()
            
            # Update UI based on new settings
            self.update_notification_badge()
            
            # Update project badges
            for project_name, project_widget in self.project_widgets.items():
                project_widget.update_notification_badge()
            
            # Show success message
            QMessageBox.information(self, "Success", "Notification settings saved successfully.")
        except Exception as e:
            warnings.warn(f"Failed to save monitoring settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
    
    def save_pr_settings(self):
        """Save PR settings."""
        try:
            # Save PR settings
            self.github_monitor.set_setting("auto_merge_md_prompt", self.auto_merge_md_prompt_checkbox.isChecked())
            self.github_monitor.config.save()
            
            # Show success message
            QMessageBox.information(self, "Success", "PR settings saved successfully.")
        except Exception as e:
            warnings.warn(f"Failed to save PR settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
    
    def show_github_settings(self):
        """Show GitHub settings dialog."""
        try:
            dialog = GitHubSettingsDialog(self.github_monitor, self)
            dialog.exec_()
        except Exception as e:
            warnings.warn(f"Failed to show GitHub settings: {e}")
    
    def show_projects_dialog(self):
        """Show GitHub projects dialog."""
        try:
            dialog = GitHubProjectsDialog(self.github_monitor, self)
            if dialog.exec_():
                self.load_pinned_projects()
        except Exception as e:
            warnings.warn(f"Failed to show GitHub projects: {e}")
    
    def toggle_notifications(self):
        """Toggle notifications panel."""
        pass
    
    def load_pinned_projects(self):
        """Load pinned projects from GitHub monitor."""
        try:
            # Clear existing project widgets
            for widget in self.project_widgets.values():
                self.projects_layout.removeWidget(widget)
                widget.deleteLater()
            self.project_widgets = {}
            
            # Add project widgets for pinned projects
            for project in self.github_monitor.projects.values():
                if project.pinned:
                    self.add_project_widget(project)
        except Exception as e:
            warnings.warn(f"Failed to load pinned projects: {e}")
    
    def add_project_widget(self, project):
        """
        Add a project widget.
        
        Args:
            project: The project to add
        """
        try:
            # Create project widget
            project_widget = ProjectIconWidget(project, self)
            
            # Add to layout
            self.projects_layout.addWidget(project_widget)
            
            # Store reference
            self.project_widgets[project.full_name] = project_widget
        except Exception as e:
            warnings.warn(f"Failed to add project widget: {e}")
    
    def add_notification(self, notification):
        """
        Add a notification.
        
        Args:
            notification: The notification to add
        """
        try:
            # Check if notifications are enabled for this type
            if notification.type == "pr" and not self.github_monitor.get_setting("notify_pr", True):
                return
            if notification.type == "branch" and not self.github_monitor.get_setting("notify_branch", True):
                return
                
            # Create notification widget
            notification_widget = NotificationWidget(notification, self)
            
            # Add to layout
            self.notifications_layout.insertWidget(0, notification_widget)
            
            # Store reference
            self.notification_widgets.append(notification_widget)
            
            # Update notification badge
            self.update_notification_badge()
        except Exception as e:
            warnings.warn(f"Failed to add notification: {e}")
    
    def add_project_notification(self, project, notification):
        """
        Add a notification to a project.
        
        Args:
            project: The project to add the notification to
            notification: The notification to add
        """
        try:
            # Update project widget if it exists
            if project.full_name in self.project_widgets:
                self.project_widgets[project.full_name].update_notification_badge()
        except Exception as e:
            warnings.warn(f"Failed to add project notification: {e}")
    
    def remove_notification(self, notification_widget):
        """
        Remove a notification.
        
        Args:
            notification_widget: The notification widget to remove
        """
        try:
            # Remove from layout
            self.notifications_layout.removeWidget(notification_widget)
            notification_widget.deleteLater()
            
            # Remove from list
            if notification_widget in self.notification_widgets:
                self.notification_widgets.remove(notification_widget)
                
            # Update notification badge
            self.update_notification_badge()
        except Exception as e:
            warnings.warn(f"Failed to remove notification: {e}")
    
    def update_notification_badge(self):
        """Update the notification badge."""
        try:
            # Count notifications
            count = len(self.notification_widgets)
            
            # Update badge text
            self.notification_badge.setText(str(count))
            
            # Show/hide badge based on count and settings
            show_badge = self.github_monitor.get_setting("show_badge", True)
            self.notification_badge.setVisible(count > 0 and show_badge)
        except Exception as e:
            warnings.warn(f"Failed to update notification badge: {e}")
    
    def clear_all_notifications(self):
        """Clear all notifications."""
        try:
            # Remove all notification widgets
            for widget in self.notification_widgets:
                self.notifications_layout.removeWidget(widget)
                widget.deleteLater()
            
            # Clear list
            self.notification_widgets = []
            
            # Update notification badge
            self.update_notification_badge()
        except Exception as e:
            warnings.warn(f"Failed to clear notifications: {e}")
    
    def clear_all_project_notifications(self):
        """Clear all notifications for all projects."""
        try:
            # Clear notifications for each project
            for project_name, project_widget in self.project_widgets.items():
                project = project_widget.project
                project.notifications = []
                project_widget.update_notification_badge()
        except Exception as e:
            warnings.warn(f"Failed to clear project notifications: {e}")
