"""
GitHub UI module.
This module provides the UI components for the GitHub plugin.
"""

import os
import logging
import webbrowser
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QToolButton, QMenu, QAction,
                           QDialog, QScrollArea, QFrame, QSizePolicy)
from PyQt5.QtGui import QIcon, QCursor, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QSize

# Import local modules
from toolkit.plugins.github.ui.github_settings import GitHubSettingsDialog
from toolkit.plugins.github.ui.github_project_ui import GitHubProjectsDialog, ProjectWidget

logger = logging.getLogger(__name__)

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
                               "ui", "icons", "notification.svg")
        if os.path.exists(icon_path):
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(icon_path).pixmap(16, 16))
            layout.addWidget(icon_label)
        else:
            # Fallback icon
            icon_label = QLabel("🔔")
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
        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.clicked.connect(self.close_notification)
        layout.addWidget(close_button)
        
        # Set widget properties
        self.setAutoFillBackground(True)
        self.setStyleSheet("""
            NotificationWidget {
                background-color: #f0f0f0;
                border-radius: 5px;
                margin-bottom: 5px;
            }
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
    
    def open_notification(self):
        """Open the notification URL in a web browser."""
        try:
            webbrowser.open(self.notification.url)
            self.notification.mark_as_read()
        except Exception as e:
            logger.error(f"Failed to open notification URL: {e}")
    
    def close_notification(self):
        """Close the notification widget."""
        self.closed.emit(self)
        self.deleteLater()

class NotificationsPanel(QWidget):
    """Panel for displaying GitHub notifications."""
    
    def __init__(self, github_manager, parent=None):
        """
        Initialize the notifications panel.
        
        Args:
            github_manager (GitHubManager): The GitHub manager instance
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.github_manager = github_manager
        
        # Set up the UI
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Notifications")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(header_label)
        
        # Clear all button
        clear_button = QPushButton("Clear All")
        clear_button.clicked.connect(self.clear_all_notifications)
        header_layout.addWidget(clear_button)
        
        layout.addLayout(header_layout)
        
        # Notifications area
        self.notifications_area = QScrollArea()
        self.notifications_area.setWidgetResizable(True)
        self.notifications_area.setFrameShape(QFrame.NoFrame)
        
        self.notifications_container = QWidget()
        self.notifications_layout = QVBoxLayout(self.notifications_container)
        self.notifications_layout.setAlignment(Qt.AlignTop)
        self.notifications_layout.setContentsMargins(0, 0, 0, 0)
        self.notifications_layout.setSpacing(5)
        
        self.notifications_area.setWidget(self.notifications_container)
        layout.addWidget(self.notifications_area)
        
        # Empty state
        self.empty_label = QLabel("No notifications")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #888;")
        self.notifications_layout.addWidget(self.empty_label)
        
        # Connect signals
        self.github_manager.notification_added.connect(self.add_notification)
    
    def add_notification(self, notification):
        """
        Add a notification to the panel.
        
        Args:
            notification (GitHubNotification): The notification to add
        """
        # Hide empty state if visible
        if self.empty_label.isVisible():
            self.empty_label.hide()
        
        # Create notification widget
        widget = NotificationWidget(notification)
        widget.closed.connect(self.remove_notification_widget)
        
        # Add to layout
        self.notifications_layout.insertWidget(0, widget)
        
        # Add to manager
        self.github_manager.add_notification_widget(widget)
    
    def remove_notification_widget(self, widget):
        """
        Remove a notification widget from the panel.
        
        Args:
            widget (NotificationWidget): The widget to remove
        """
        self.github_manager.remove_notification_widget(widget)
        
        # Show empty state if no notifications
        if self.notifications_layout.count() == 1:  # Only empty label
            self.empty_label.show()
    
    def clear_all_notifications(self):
        """Clear all notifications."""
        # Remove all notification widgets
        for i in reversed(range(self.notifications_layout.count())):
            item = self.notifications_layout.itemAt(i)
            if item and item.widget() != self.empty_label:
                widget = item.widget()
                self.notifications_layout.removeWidget(widget)
                widget.deleteLater()
        
        # Clear notifications in manager
        self.github_manager.clear_all_notifications()
        
        # Show empty state
        self.empty_label.show()

class GitHubUI(QObject):
    """Main UI class for the GitHub plugin."""
    
    def __init__(self, github_manager, toolbar, parent=None):
        """
        Initialize the GitHub UI.
        
        Args:
            github_manager (GitHubManager): The GitHub manager instance
            toolbar: The toolbar instance
            parent (QObject, optional): Parent object
        """
        super().__init__(parent)
        self.github_manager = github_manager
        self.toolbar = toolbar
        self.toolbar_button = None
        self.notification_badge = None
        self.settings_dialog = None
        self.projects_dialog = None
        self.notifications_panel = None
        
        # Initialize UI components
        self._init_ui()
        
        # Connect signals
        self.github_manager.notification_added.connect(self.update_notification_badge)
        self.github_manager.project_added.connect(self.on_project_added)
        self.github_manager.project_removed.connect(self.on_project_removed)
    
    def _init_ui(self):
        """Initialize UI components."""
        # Create toolbar button
        self.toolbar_button = QToolButton()
        self.toolbar_button.setIcon(self._get_github_icon())
        self.toolbar_button.setIconSize(QSize(24, 24))
        self.toolbar_button.setToolTip("GitHub")
        self.toolbar_button.clicked.connect(self.show_menu)
        
        # Create notification badge
        self.notification_badge = QLabel("0")
        self.notification_badge.setStyleSheet("""
            background-color: red;
            color: white;
            border-radius: 10px;
            padding: 2px;
            font-size: 10px;
        """)
        self.notification_badge.setFixedSize(16, 16)
        self.notification_badge.setAlignment(Qt.AlignCenter)
        self.notification_badge.hide()
        
        # Create notifications panel
        self.notifications_panel = NotificationsPanel(self.github_manager)
        
        # Load pinned projects
        self.github_manager.load_pinned_projects()
    
    def _get_github_icon(self):
        """Get the GitHub icon."""
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "ui", "icons", "github.svg")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        else:
            # Create a fallback icon
            return QIcon.fromTheme("github", QIcon.fromTheme("web-browser"))
    
    def add_to_toolbar(self):
        """Add the GitHub button to the toolbar."""
        if self.toolbar and self.toolbar_button:
            # Add to middle of toolbar
            self.toolbar.add_widget_to_center(self.toolbar_button)
            
            # Add notification badge
            if self.notification_badge:
                self.toolbar.add_badge_to_widget(self.toolbar_button, self.notification_badge)
    
    def remove_from_toolbar(self):
        """Remove the GitHub button from the toolbar."""
        if self.toolbar and self.toolbar_button:
            self.toolbar.remove_widget(self.toolbar_button)
    
    def show_menu(self):
        """Show the GitHub menu."""
        menu = QMenu()
        
        # Settings action
        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self.show_settings)
        
        # Projects action
        projects_action = menu.addAction("Projects")
        projects_action.triggered.connect(self.show_projects)
        
        # Notifications action
        notifications_action = menu.addAction("Notifications")
        notifications_action.triggered.connect(self.show_notifications)
        
        # Separator
        menu.addSeparator()
        
        # Clear notifications action
        clear_action = menu.addAction("Clear All Notifications")
        clear_action.triggered.connect(self.github_manager.clear_all_notifications)
        
        # Show menu
        menu.exec_(QCursor.pos())
    
    def show_settings(self):
        """Show the GitHub settings dialog."""
        if not self.settings_dialog:
            self.settings_dialog = GitHubSettingsDialog(self.github_manager.github_monitor)
        
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()
    
    def show_projects(self):
        """Show the GitHub projects dialog."""
        if not self.projects_dialog:
            self.projects_dialog = GitHubProjectsDialog(self.github_manager)
        
        self.projects_dialog.show()
        self.projects_dialog.raise_()
        self.projects_dialog.activateWindow()
    
    def show_notifications(self):
        """Show the notifications panel."""
        dialog = QDialog()
        dialog.setWindowTitle("GitHub Notifications")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(self.notifications_panel)
        
        dialog.exec_()
    
    def update_notification_badge(self):
        """Update the notification badge."""
        # Count unread notifications
        count = 0
        for project in self.github_manager.github_monitor.projects:
            count += len([n for n in project.notifications if not n.read])
        
        # Update badge
        if count > 0:
            self.notification_badge.setText(str(count))
            self.notification_badge.show()
        else:
            self.notification_badge.hide()
    
    def on_project_added(self, project):
        """
        Handle a project being added.
        
        Args:
            project (GitHubProject): The project that was added
        """
        # Create project widget
        widget = ProjectWidget(project, self.github_manager)
        
        # Add to toolbar
        if self.toolbar:
            self.toolbar.add_widget(widget)
        
        # Add to manager
        self.github_manager.project_widgets[project.full_name] = widget
    
    def on_project_removed(self, project):
        """
        Handle a project being removed.
        
        Args:
            project (GitHubProject): The project that was removed
        """
        # Remove from toolbar
        if project.full_name in self.github_manager.project_widgets:
            widget = self.github_manager.project_widgets[project.full_name]
            if self.toolbar:
                self.toolbar.remove_widget(widget)
