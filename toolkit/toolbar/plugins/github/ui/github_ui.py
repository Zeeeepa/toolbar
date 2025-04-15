import os
import webbrowser
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QToolButton, QMenu, QAction,
                           QSizePolicy, QFrame, QScrollArea)
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QSize

from .github_project_ui import ProjectWidget, ProjectSettingsDialog, GitHubProjectsDialog
from .github_settings import GitHubSettingsDialog

# Configure logging
logger = logging.getLogger(__name__)

class NotificationWidget(QWidget):
    """Widget for displaying a GitHub notification."""
    
    closed = pyqtSignal(object)  # Emits self when closed
    
    def __init__(self, notification, parent=None):
        """
        Initialize a notification widget.
        
        Args:
            notification: The notification to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.notification = notification
        
        # Set up the UI
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Notification icon
        icon_label = QLabel()
        if notification.type == "pr":
            icon = QIcon.fromTheme("document-edit", QIcon.fromTheme("edit"))
        elif notification.type == "branch":
            icon = QIcon.fromTheme("vcs-branch", QIcon.fromTheme("fork"))
        else:
            icon = QIcon.fromTheme("dialog-information", QIcon.fromTheme("info"))
        
        icon_label.setPixmap(icon.pixmap(16, 16))
        layout.addWidget(icon_label)
        
        # Notification text
        text_label = QLabel(notification.title)
        text_label.setWordWrap(True)
        layout.addWidget(text_label, 1)
        
        # Open button
        open_button = QPushButton("Open")
        open_button.setMaximumWidth(60)
        open_button.clicked.connect(self.open_notification)
        layout.addWidget(open_button)
        
        # Close button
        close_button = QPushButton("Dismiss")
        close_button.setMaximumWidth(60)
        close_button.clicked.connect(self.close_notification)
        layout.addWidget(close_button)
        
        # Set cursor to pointing hand
        self.setCursor(Qt.PointingHandCursor)
        
        # Set background color based on read status
        self.update_style()
    
    def update_style(self):
        """Update widget style based on notification read status."""
        if self.notification.read:
            self.setStyleSheet("background-color: #f0f0f0; border-radius: 4px;")
        else:
            self.setStyleSheet("background-color: #e1f5fe; border-radius: 4px;")
    
    def open_notification(self):
        """Open the notification URL in a browser."""
        webbrowser.open(self.notification.url)
        self.notification.read = True
        self.update_style()
    
    def close_notification(self):
        """Close the notification."""
        self.closed.emit(self)
        self.deleteLater()

class GitHubUI(QWidget):
    """UI component for GitHub functionality in the taskbar."""
    
    def __init__(self, github_monitor, parent=None):
        """
        Initialize the GitHub UI.
        
        Args:
            github_monitor: The GitHub monitor instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.github_monitor = github_monitor
        
        # Initialize collections
        self.notification_widgets = []
        self.project_widgets = {}
        
        # Set up UI
        self.init_ui()
        
        # Connect signals
        self.github_monitor.notification_received.connect(self.add_github_notification)
        self.github_monitor.project_notification_received.connect(self.add_project_notification)
        self.github_monitor.data_refreshed.connect(self.update_notification_badge)
        
        # Load pinned projects
        self.load_pinned_projects()
        
        # Start monitoring if credentials are set
        if self.github_monitor.username and self.github_monitor.api_token:
            self.github_monitor.start_monitoring()
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # GitHub icon button (centered in the taskbar)
        self.github_button = QToolButton()
        self.github_button.setIcon(QIcon.fromTheme("github", QIcon.fromTheme("folder-github")))
        self.github_button.setIconSize(QSize(24, 24))
        self.github_button.setToolTip("GitHub")
        self.github_button.clicked.connect(self.toggle_github_panel)
        
        # Notification badge
        self.notification_badge = QLabel("0")
        self.notification_badge.setStyleSheet(
            "background-color: red; color: white; border-radius: 10px; padding: 2px;"
        )
        self.notification_badge.setAlignment(Qt.AlignCenter)
        self.notification_badge.setVisible(False)
        
        # Add GitHub button to layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addStretch()
        button_layout.addWidget(self.github_button)
        button_layout.addWidget(self.notification_badge)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # GitHub panel (hidden by default)
        self.github_panel = QWidget()
        self.github_panel.setVisible(False)
        panel_layout = QVBoxLayout(self.github_panel)
        panel_layout.setContentsMargins(10, 10, 10, 10)
        
        # Panel header
        header_layout = QHBoxLayout()
        header_label = QLabel("<b>GitHub</b>")
        header_layout.addWidget(header_label)
        
        # Settings button
        settings_button = QToolButton()
        settings_button.setIcon(QIcon.fromTheme("configure", QIcon.fromTheme("settings")))
        settings_button.setToolTip("GitHub Settings")
        settings_button.clicked.connect(self.show_github_settings)
        header_layout.addWidget(settings_button)
        
        # Projects button
        projects_button = QToolButton()
        projects_button.setIcon(QIcon.fromTheme("folder-github", QIcon.fromTheme("folder")))
        projects_button.setToolTip("GitHub Projects")
        projects_button.clicked.connect(self.show_projects_dialog)
        header_layout.addWidget(projects_button)
        
        # Refresh button
        refresh_button = QToolButton()
        refresh_button.setIcon(QIcon.fromTheme("view-refresh", QIcon.fromTheme("refresh")))
        refresh_button.setToolTip("Refresh GitHub Data")
        refresh_button.clicked.connect(self.refresh_github_data)
        header_layout.addWidget(refresh_button)
        
        # Close button
        close_button = QToolButton()
        close_button.setIcon(QIcon.fromTheme("window-close", QIcon.fromTheme("close")))
        close_button.setToolTip("Close Panel")
        close_button.clicked.connect(lambda: self.github_panel.setVisible(False))
        header_layout.addWidget(close_button)
        
        panel_layout.addLayout(header_layout)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        panel_layout.addWidget(separator)
        
        # Pinned projects section
        projects_label = QLabel("Pinned Projects:")
        panel_layout.addWidget(projects_label)
        
        self.projects_container = QWidget()
        self.projects_layout = QHBoxLayout(self.projects_container)
        self.projects_layout.setContentsMargins(0, 0, 0, 0)
        self.projects_layout.setSpacing(5)
        self.projects_layout.setAlignment(Qt.AlignLeft)
        
        panel_layout.addWidget(self.projects_container)
        
        # Add another separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        panel_layout.addWidget(separator2)
        
        # Notifications section
        notifications_header = QHBoxLayout()
        notifications_label = QLabel("Recent Notifications:")
        notifications_header.addWidget(notifications_label)
        
        clear_all_button = QPushButton("Clear All")
        clear_all_button.clicked.connect(self.clear_all_notifications)
        notifications_header.addWidget(clear_all_button)
        
        panel_layout.addLayout(notifications_header)
        
        # Notifications scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.notifications_container = QWidget()
        self.notifications_layout = QVBoxLayout(self.notifications_container)
        self.notifications_layout.setContentsMargins(0, 0, 0, 0)
        self.notifications_layout.setSpacing(5)
        self.notifications_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self.notifications_container)
        panel_layout.addWidget(scroll_area)
        
        # Add panel to main layout
        main_layout.addWidget(self.github_panel)
    
    def toggle_github_panel(self):
        """Toggle the GitHub panel visibility."""
        self.github_panel.setVisible(not self.github_panel.isVisible())
    
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
    
    def refresh_github_data(self):
        """Refresh GitHub data."""
        self.github_monitor.check_github_updates()
    
    def add_github_notification(self, notification):
        """
        Add a GitHub notification.
        
        Args:
            notification: The notification to add
        """
        # Create notification widget
        notification_widget = NotificationWidget(notification, self)
        notification_widget.closed.connect(self.remove_notification)
        
        # Add to layout
        self.notifications_layout.insertWidget(0, notification_widget)
        self.notification_widgets.append(notification_widget)
        
        # Update notification badge
        self.update_notification_badge()
    
    def add_project_notification(self, project, notification):
        """
        Add a notification to a project.
        
        Args:
            project: The project to add the notification to
            notification: The notification to add
        """
        # Update project widget if it exists
        if project.full_name in self.project_widgets:
            self.project_widgets[project.full_name].update()
        
        # Update notification badge
        self.update_notification_badge()
    
    def remove_notification(self, notification_widget):
        """
        Remove a notification.
        
        Args:
            notification_widget: The notification widget to remove
        """
        if notification_widget in self.notification_widgets:
            self.notification_widgets.remove(notification_widget)
            self.notifications_layout.removeWidget(notification_widget)
            notification_widget.deleteLater()
            
            # Update notification badge
            self.update_notification_badge()
    
    def clear_all_notifications(self):
        """Remove all notifications."""
        # Remove all notifications
        while self.notification_widgets:
            notification_widget = self.notification_widgets.pop()
            self.notifications_layout.removeWidget(notification_widget)
            notification_widget.deleteLater()
        
        # Clear all project notifications
        self.github_monitor.clear_all_notifications()
        
        # Update project widgets
        for widget in self.project_widgets.values():
            widget.update()
        
        # Update notification badge
        self.update_notification_badge()
    
    def update_notification_badge(self):
        """Update the notification badge count."""
        # Count all unread notifications
        unread_count = 0
        
        # Count notifications in the notification panel
        for widget in self.notification_widgets:
            if not widget.notification.read:
                unread_count += 1
        
        # Count notifications in projects
        for project in self.github_monitor.get_projects():
            for notification in project.notifications:
                if not notification.read:
                    unread_count += 1
        
        # Update badge
        self.notification_badge.setText(str(unread_count))
        self.notification_badge.setVisible(unread_count > 0)
    
    def load_pinned_projects(self):
        """Load pinned projects from GitHub monitor."""
        # Clear existing project widgets
        for widget in self.project_widgets.values():
            self.projects_layout.removeWidget(widget)
            widget.deleteLater()
        self.project_widgets = {}
        
        # Add widgets for pinned projects
        for project in self.github_monitor.get_pinned_projects():
            self.add_project_widget(project)
    
    def add_project_widget(self, project):
        """
        Add a project widget.
        
        Args:
            project: The project to add
        """
        # Create project widget
        project_widget = ProjectWidget(project, self)
        project_widget.clicked.connect(self.handle_project_clicked)
        project_widget.settings_clicked.connect(self.show_project_settings)
        
        # Add to layout
        self.projects_layout.addWidget(project_widget)
        self.project_widgets[project.full_name] = project_widget
    
    def remove_project_widget(self, widget):
        """
        Remove a project widget.
        
        Args:
            widget: The project widget to remove
        """
        project = widget.project
        if project.full_name in self.project_widgets:
            self.projects_layout.removeWidget(widget)
            widget.deleteLater()
            del self.project_widgets[project.full_name]
            
            # Unpin the project in the monitor
            self.github_monitor.pin_project(project.full_name, False)
    
    def handle_project_clicked(self, project):
        """
        Handle project widget clicked.
        
        Args:
            project: The project that was clicked
        """
        # If there are unread notifications, show them
        unread_notifications = [n for n in project.notifications if not n.read]
        if unread_notifications:
            # Open the first unread notification
            notification = unread_notifications[0]
            webbrowser.open(notification.url)
            notification.read = True
            
            # Update the project widget
            if project.full_name in self.project_widgets:
                self.project_widgets[project.full_name].update()
            
            # Update notification badge
            self.update_notification_badge()
        else:
            # Otherwise open the project page
            webbrowser.open(project.url)
    
    def show_project_settings(self, project):
        """
        Show project settings dialog.
        
        Args:
            project: The project to show settings for
        """
        dialog = ProjectSettingsDialog(project, self.github_monitor, self)
        dialog.exec_()
        
        # Update the project widget
        if project.full_name in self.project_widgets:
            self.project_widgets[project.full_name].update()
