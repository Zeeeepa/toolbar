import os
import warnings
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QObject, pyqtSignal

# Update the import to use the new github module structure
from Toolbar.core.github import GitHubMonitor, GitHubProject, GitHubNotification

class GitHubManager(QObject):
    """
    Manager class for GitHub functionality.
    This class encapsulates all GitHub-related functionality that was previously in the toolbar.
    """
    
    def __init__(self, github_monitor, parent=None):
        """
        Initialize the GitHub manager.
        
        Args:
            github_monitor (GitHubMonitor): The GitHub monitor instance
            parent (QObject, optional): Parent object
        """
        super().__init__(parent)
        self.github_monitor = github_monitor
        self.notification_widgets = []
        self.project_widgets = {}
        
    def add_github_notification(self, notification):
        """
        Add a GitHub notification.
        
        Args:
            notification (GitHubNotification): The notification to add
        """
        # This method would be implemented by the UI component that displays notifications
        pass
        
    def add_project_notification(self, project, notification):
        """
        Add a notification to a project.
        
        Args:
            project (GitHubProject): The project to add the notification to
            notification (GitHubNotification): The notification to add
        """
        # Update project widget if it exists
        if project.full_name in self.project_widgets:
            self.project_widgets[project.full_name].update_notification_badge()
    
    def remove_notification(self, notification_widget):
        """
        Remove a notification.
        
        Args:
            notification_widget: The notification widget to remove
        """
        if notification_widget in self.notification_widgets:
            self.notification_widgets.remove(notification_widget)
            
    def clear_all_notifications(self):
        """Remove all notifications."""
        self.notification_widgets = []
        
    def clear_all_project_notifications(self):
        """Clear all notifications for all projects."""
        for project_name, project_widget in self.project_widgets.items():
            project = project_widget.project
            project.notifications = []
            project_widget.update_notification_badge()
    
    def load_pinned_projects(self):
        """Load pinned projects from GitHub monitor."""
        # This method would be implemented by the UI component that displays projects
        pass
    
    def add_project_widget(self, project):
        """
        Add a project widget.
        
        Args:
            project (GitHubProject): The project to add
        """
        # This method would be implemented by the UI component that displays projects
        pass
    
    def remove_project_widget(self, widget):
        """
        Remove a project widget.
        
        Args:
            widget: The project widget to remove
        """
        project = widget.project
        if project.full_name in self.project_widgets:
            del self.project_widgets[project.full_name]
            
            # Save projects
            try:
                self.github_monitor.save_projects()
            except Exception as e:
                warnings.warn(f"Failed to save projects: {e}")
    
    def save_projects(self):
        """Save GitHub projects."""
        try:
            self.github_monitor.save_projects()
        except Exception as e:
            warnings.warn(f"Failed to save projects: {e}")
