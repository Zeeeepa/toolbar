import os
import warnings
import webbrowser
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QToolButton, QMenu, QAction)
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import Qt, pyqtSignal

from Toolbar.core.github_manager import GitHubManager
from Toolbar.ui.github_project_ui import ProjectWidget, GitHubProjectsDialog
from Toolbar.ui.github_settings import GitHubSettingsDialog

class NotificationWidget(QWidget):
    """Widget for displaying a GitHub notification."""
    
    closed = pyqtSignal(object)  # Emits self when closed
    
    def __init__(self, notification, parent=None):
        """
        Initialize a notification widget.
        
        Args:
            notification (GitHubNotification): The notification to display
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.notification = notification
        
        # Set up the UI
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Notification icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "icons", "notification.svg")
        if os.path.exists(icon_path):
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(icon_path).pixmap(16, 16))
            layout.addWidget(icon_label)
        
        # Notification text
        text_label = QLabel(notification.title)
        text_label.setWordWrap(True)
        layout.addWidget(text_label, 1)
        
        # Open button
        open_button = QPushButton("Open")
        open_button.clicked.connect(self.open_notification)
        layout.addWidget(open_button)
        
        # Close button
        close_button = QPushButton("Dismiss")
        close_button.clicked.connect(self.close_notification)
        layout.addWidget(close_button)
        
        # Set cursor to pointing hand
        self.setCursor(Qt.PointingHandCursor)
    
    def open_notification(self):
        """Open the notification URL in a browser."""
        webbrowser.open(self.notification.url)
    
    def close_notification(self):
        """Close the notification."""
        self.closed.emit(self)
        self.deleteLater()

class GitHubUI(QWidget):
    """UI component for GitHub functionality."""
    
    def __init__(self, github_monitor, parent=None):
        """
        Initialize the GitHub UI.
        
        Args:
            github_monitor (GitHubMonitor): The GitHub monitor instance
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        
        # Create GitHub manager
        self.github_manager = GitHubManager(github_monitor, self)
        self.github_monitor = github_monitor
        
        # Set up UI
        self.init_ui()
        
        # Connect signals
        self.github_monitor.notification_received.connect(self.add_github_notification)
        self.github_monitor.project_notification_received.connect(self.add_project_notification)
        
        # Load pinned projects
        self.load_pinned_projects()
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar for GitHub actions
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(toolbar_layout)
        
        # GitHub settings button
        settings_button = QToolButton()
        settings_button.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                "icons", "settings.svg")))
        settings_button.setToolTip("GitHub Settings")
        settings_button.clicked.connect(self.show_github_settings)
        toolbar_layout.addWidget(settings_button)
        
        # Projects button
        projects_button = QToolButton()
        projects_button.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                "icons", "project.svg")))
        projects_button.setToolTip("GitHub Projects")
        projects_button.clicked.connect(self.show_projects_dialog)
        toolbar_layout.addWidget(projects_button)
        
        # Notifications button
        self.notifications_button = QToolButton()
        self.notifications_button.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                        "icons", "notification.svg")))
        self.notifications_button.setToolTip("GitHub Notifications")
        self.notifications_button.clicked.connect(self.toggle_notifications)
        toolbar_layout.addWidget(self.notifications_button)
        
        # Notification badge
        self.notification_badge = QLabel("0")
        self.notification_badge.setStyleSheet("background-color: red; color: white; border-radius: 10px; padding: 2px;")
        self.notification_badge.setAlignment(Qt.AlignCenter)
        self.notification_badge.setVisible(False)
        toolbar_layout.addWidget(self.notification_badge)
        
        # Spacer
        toolbar_layout.addStretch(1)
        
        # Projects container
        projects_container = QWidget()
        self.projects_layout = QHBoxLayout(projects_container)
        self.projects_layout.setContentsMargins(0, 0, 0, 0)
        self.projects_layout.setSpacing(5)
        main_layout.addWidget(projects_container)
        
        # Notification container
        self.notification_container = QWidget()
        self.notification_container.setVisible(False)
        notification_container_layout = QVBoxLayout(self.notification_container)
        notification_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Notification header
        notification_header = QWidget()
        notification_header_layout = QHBoxLayout(notification_header)
        notification_header_layout.setContentsMargins(5, 5, 5, 5)
        
        notification_header_label = QLabel("GitHub Notifications")
        notification_header_layout.addWidget(notification_header_label)
        
        clear_all_button = QPushButton("Clear All")
        clear_all_button.clicked.connect(self.clear_all_notifications)
        notification_header_layout.addWidget(clear_all_button)
        
        notification_container_layout.addWidget(notification_header)
        
        # Notification list
        notification_list = QWidget()
        self.notification_layout = QVBoxLayout(notification_list)
        self.notification_layout.setContentsMargins(0, 0, 0, 0)
        self.notification_layout.setSpacing(0)
        notification_container_layout.addWidget(notification_list)
        
        main_layout.addWidget(self.notification_container)
        
        # Initialize collections
        self.notification_widgets = []
        self.project_widgets = {}
    
    def show_github_settings(self):
        """Show GitHub settings dialog."""
        dialog = GitHubSettingsDialog(self.github_monitor, self)
        dialog.exec_()
    
    def show_projects_dialog(self):
        """Show GitHub projects dialog."""
        dialog = GitHubProjectsDialog(self.github_monitor, self)
        if dialog.exec_():
            # Reload pinned projects
            self.load_pinned_projects()
    
    def toggle_notifications(self):
        """Toggle notification panel visibility."""
        self.notification_container.setVisible(not self.notification_container.isVisible())
    
    def add_github_notification(self, notification):
        """
        Add a GitHub notification.
        
        Args:
            notification (GitHubNotification): The notification to add
        """
        # Create notification widget
        notification_widget = NotificationWidget(notification, self)
        notification_widget.closed.connect(self.remove_notification)
        
        # Add to layout
        self.notification_layout.insertWidget(0, notification_widget)
        self.notification_widgets.append(notification_widget)
        
        # Update notification badge
        self.update_notification_badge()
        
        # Update GitHub manager
        self.github_manager.notification_widgets = self.notification_widgets
    
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
        
        # Update GitHub manager
        self.github_manager.project_widgets = self.project_widgets
    
    def remove_notification(self, notification_widget):
        """
        Remove a notification.
        
        Args:
            notification_widget (NotificationWidget): The notification widget to remove
        """
        if notification_widget in self.notification_widgets:
            self.notification_widgets.remove(notification_widget)
            self.notification_layout.removeWidget(notification_widget)
            notification_widget.deleteLater()
            
            # Update notification badge
            self.update_notification_badge()
            
            # Update GitHub manager
            self.github_manager.notification_widgets = self.notification_widgets
    
    def clear_all_notifications(self):
        """Remove all notifications."""
        # Remove all notifications
        while self.notification_widgets:
            notification_widget = self.notification_widgets.pop()
            self.notification_layout.removeWidget(notification_widget)
            notification_widget.deleteLater()
        
        # Update notification badge
        self.update_notification_badge()
        
        # Hide notification container if visible
        if self.notification_container.isVisible():
            self.notification_container.setVisible(False)
        
        # Update GitHub manager
        self.github_manager.notification_widgets = self.notification_widgets
    
    def clear_all_project_notifications(self):
        """Clear all notifications for all projects."""
        for project_name, project_widget in self.project_widgets.items():
            project = project_widget.project
            project.notifications = []
            project_widget.update_notification_badge()
        
        # Update GitHub manager
        self.github_manager.project_widgets = self.project_widgets
    
    def update_notification_badge(self):
        """Update the notification badge count."""
        count = len(self.notification_widgets)
        self.notification_badge.setText(str(count))
        self.notification_badge.setVisible(count > 0)
    
    def load_pinned_projects(self):
        """Load pinned projects from GitHub monitor."""
        # Clear existing project widgets
        for widget in self.project_widgets.values():
            self.projects_layout.removeWidget(widget)
            widget.deleteLater()
        self.project_widgets = {}
        
        # Add widgets for pinned projects
        for project in self.github_monitor.get_projects():
            if project.pinned:
                self.add_project_widget(project)
        
        # Update GitHub manager
        self.github_manager.project_widgets = self.project_widgets
    
    def add_project_widget(self, project):
        """
        Add a project widget.
        
        Args:
            project (GitHubProject): The project to add
        """
        # Create project widget
        project_widget = ProjectWidget(project, self)
        
        # Add to layout
        self.projects_layout.addWidget(project_widget)
        self.project_widgets[project.full_name] = project_widget
        
        # Update GitHub manager
        self.github_manager.project_widgets = self.project_widgets
    
    def remove_project_widget(self, widget):
        """
        Remove a project widget.
        
        Args:
            widget (ProjectWidget): The project widget to remove
        """
        project = widget.project
        if project.full_name in self.project_widgets:
            self.projects_layout.removeWidget(widget)
            widget.deleteLater()
            del self.project_widgets[project.full_name]
            
            # Save projects
            try:
                self.github_monitor.save_projects()
            except Exception as e:
                warnings.warn(f"Failed to save projects: {e}")
            
            # Update GitHub manager
            self.github_manager.project_widgets = self.project_widgets
