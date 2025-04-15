import os
import warnings
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QObject, pyqtSignal

# Import local modules
from toolkit.plugins.github.github.monitor import GitHubMonitor
from toolkit.plugins.github.github.models import GitHubProject, GitHubNotification

logger = logging.getLogger(__name__)

class GitHubManager(QObject):
    """
    Manager class for GitHub functionality.
    This class encapsulates all GitHub-related functionality for the toolkit.
    """
    
    notification_added = pyqtSignal(object)  # Emitted when a notification is added
    project_added = pyqtSignal(object)  # Emitted when a project is added
    project_removed = pyqtSignal(object)  # Emitted when a project is removed
    
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
        
        # Connect signals from monitor
        self.github_monitor.notification_received.connect(self.on_notification_received)
        self.github_monitor.project_notification_received.connect(self.on_project_notification_received)
    
    def on_notification_received(self, notification):
        """
        Handle a new notification from the monitor.
        
        Args:
            notification (GitHubNotification): The notification received
        """
        self.notification_added.emit(notification)
    
    def on_project_notification_received(self, project, notification):
        """
        Handle a new project notification from the monitor.
        
        Args:
            project (GitHubProject): The project that received a notification
            notification (GitHubNotification): The notification received
        """
        # Update project widget if it exists
        if project.full_name in self.project_widgets:
            self.project_widgets[project.full_name].update_notification_badge()
    
    def add_notification_widget(self, widget):
        """
        Add a notification widget to the manager.
        
        Args:
            widget: The notification widget to add
        """
        self.notification_widgets.append(widget)
    
    def remove_notification_widget(self, widget):
        """
        Remove a notification widget from the manager.
        
        Args:
            widget: The notification widget to remove
        """
        if widget in self.notification_widgets:
            self.notification_widgets.remove(widget)
    
    def clear_all_notifications(self):
        """Remove all notifications."""
        self.notification_widgets = []
        self.github_monitor.clear_all_notifications()
    
    def clear_project_notifications(self, project):
        """
        Clear all notifications for a project.
        
        Args:
            project (GitHubProject): The project to clear notifications for
        """
        project.clear_notifications()
        if project.full_name in self.project_widgets:
            self.project_widgets[project.full_name].update_notification_badge()
        self.github_monitor.save_projects()
    
    def clear_all_project_notifications(self):
        """Clear all notifications for all projects."""
        for project_name, project_widget in self.project_widgets.items():
            project = project_widget.project
            project.clear_notifications()
            project_widget.update_notification_badge()
        self.github_monitor.save_projects()
    
    def load_pinned_projects(self):
        """Load pinned projects from GitHub monitor."""
        for project in self.github_monitor.projects:
            if project.pinned:
                self.add_project_widget(project)
    
    def add_project_widget(self, project):
        """
        Add a project widget to the manager.
        
        Args:
            project (GitHubProject): The project to add
        """
        if project.full_name in self.project_widgets:
            return self.project_widgets[project.full_name]
        
        # This would be implemented by the UI component
        self.project_added.emit(project)
        return None
    
    def remove_project_widget(self, widget):
        """
        Remove a project widget from the manager.
        
        Args:
            widget: The project widget to remove
        """
        project = widget.project
        if project.full_name in self.project_widgets:
            del self.project_widgets[project.full_name]
            
            # Unpin project
            self.github_monitor.pin_project(project, False)
            
            # Emit signal
            self.project_removed.emit(project)
    
    def get_user_repositories(self):
        """Get repositories for the authenticated user."""
        return self.github_monitor.get_user_repositories()
    
    def pin_project(self, project, pinned=True):
        """
        Pin or unpin a project.
        
        Args:
            project (GitHubProject): The project to pin/unpin
            pinned (bool, optional): Whether to pin or unpin the project
        """
        self.github_monitor.pin_project(project, pinned)
        
        # Add or remove project widget
        if pinned:
            self.add_project_widget(project)
        else:
            if project.full_name in self.project_widgets:
                widget = self.project_widgets[project.full_name]
                self.remove_project_widget(widget)
    
    def save_projects(self):
        """Save GitHub projects."""
        try:
            self.github_monitor.save_projects()
        except Exception as e:
            logger.error(f"Failed to save projects: {e}")
    
    def validate_credentials(self):
        """Validate GitHub credentials."""
        return self.github_monitor.validate_credentials()
    
    def start_monitoring(self):
        """Start monitoring GitHub repositories."""
        self.github_monitor.start_monitoring()
    
    def stop_monitoring(self):
        """Stop monitoring GitHub repositories."""
        self.github_monitor.stop_monitoring()
