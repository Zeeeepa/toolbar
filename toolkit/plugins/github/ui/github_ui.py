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
        layout.setContentsMargins(10, 10, 10, 10)
        
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
        
        # Notifications scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        self.notifications_widget = QWidget()
        self.notifications_layout = QVBoxLayout(self.notifications_widget)
        self.notifications_layout.setContentsMargins(0, 0, 0, 0)
        self.notifications_layout.setSpacing(5)
        self.notifications_layout.addStretch()
        
        scroll_area.setWidget(self.notifications_widget)
        layout.addWidget(scroll_area)
        
        # Set widget properties
        self.setMinimumWidth(300)
        self.setMaximumHeight(400)
    
    def add_notification(self, notification):
        """
        Add a notification to the panel.
        
        Args:
            notification (GitHubNotification): The notification to add
        """
        notification_widget = NotificationWidget(notification, self)
        notification_widget.closed.connect(self.remove_notification)
        
        # Insert at the top (before the stretch)
        self.notifications_layout.insertWidget(0, notification_widget)
        
        # Add to manager
        self.github_manager.add_notification_widget(notification_widget)
    
    def remove_notification(self, widget):
        """
        Remove a notification from the panel.
        
        Args:
            widget (NotificationWidget): The notification widget to remove
        """
        self.github_manager.remove_notification_widget(widget)
    
    def clear_all_notifications(self):
        """Clear all notifications."""
        # Remove all notification widgets
        while self.notifications_layout.count() > 1:  # Keep the stretch
            item = self.notifications_layout.itemAt(0)
            if item.widget():
                item.widget().deleteLater()
            self.notifications_layout.removeItem(item)
        
        # Clear notifications in manager
        self.github_manager.clear_all_notifications()

class GitHubUI(QWidget):
    """UI component for GitHub functionality."""
    
    def __init__(self, github_manager, toolbar=None, parent=None):
        """
        Initialize the GitHub UI.
        
        Args:
            github_manager (GitHubManager): The GitHub manager instance
            toolbar: The toolbar to add the GitHub icon to
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        
        self.github_manager = github_manager
        self.toolbar = toolbar
        self.github_monitor = github_manager.github_monitor
        
        # GitHub button
        self.github_button = None
        
        # Notifications panel
        self.notifications_panel = NotificationsPanel(github_manager, self)
        self.notifications_panel.hide()
        
        # Connect signals
        self.github_manager.notification_added.connect(self.on_notification_added)
        self.github_manager.project_added.connect(self.on_project_added)
        self.github_manager.project_removed.connect(self.on_project_removed)
        
        # Load pinned projects
        self.github_manager.load_pinned_projects()
    
    def add_to_toolbar(self, position='right'):
        """
        Add the GitHub icon to the toolbar.
        
        Args:
            position (str): Position in the toolbar ('left', 'middle', 'right')
        """
        if not self.toolbar:
            logger.warning("No toolbar available to add GitHub icon")
            return
        
        # Create GitHub button
        self.github_button = QToolButton()
        
        # Load icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "ui", "icons", "github.svg")
        if os.path.exists(icon_path):
            self.github_button.setIcon(QIcon(icon_path))
        else:
            # Fallback text
            self.github_button.setText("GH")
        
        self.github_button.setIconSize(QSize(24, 24))
        self.github_button.setToolTip("GitHub")
        
        # Set up context menu
        self.github_button.setPopupMode(QToolButton.InstantPopup)
        self.setup_context_menu()
        
        # Add to toolbar based on position
        if position == 'middle':
            # Add to middle of toolbar
            self.toolbar.add_widget_to_center(self.github_button)
        elif position == 'left':
            # Add to left side of toolbar
            self.toolbar.add_widget_to_left(self.github_button)
        else:
            # Add to right side of toolbar (default)
            self.toolbar.add_widget_to_right(self.github_button)
        
        # Add notification badge
        self.notification_badge = QLabel("0")
        self.notification_badge.setStyleSheet("""
            background-color: red;
            color: white;
            border-radius: 8px;
            padding: 2px;
            font-size: 10px;
        """)
        self.notification_badge.setFixedSize(16, 16)
        self.notification_badge.setAlignment(Qt.AlignCenter)
        self.notification_badge.hide()
        
        # Add badge to toolbar
        if hasattr(self.toolbar, 'add_badge_to_widget'):
            self.toolbar.add_badge_to_widget(self.github_button, self.notification_badge)
    
    def remove_from_toolbar(self):
        """Remove the GitHub icon from the toolbar."""
        if self.toolbar and self.github_button:
            self.toolbar.remove_widget(self.github_button)
            self.github_button = None
    
    def setup_context_menu(self):
        """Set up the context menu for the GitHub button."""
        menu = QMenu()
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        # Projects action
        projects_action = QAction("Projects", self)
        projects_action.triggered.connect(self.show_projects)
        menu.addAction(projects_action)
        
        # Notifications action
        notifications_action = QAction("Notifications", self)
        notifications_action.triggered.connect(self.toggle_notifications_panel)
        menu.addAction(notifications_action)
        
        # Clear notifications action
        clear_action = QAction("Clear Notifications", self)
        clear_action.triggered.connect(self.clear_all_notifications)
        menu.addAction(clear_action)
        
        # Set menu
        self.github_button.setMenu(menu)
    
    def show_settings(self):
        """Show the GitHub settings dialog."""
        dialog = GitHubSettingsDialog(self.github_monitor, self)
        dialog.exec_()
        
        # Restart monitoring if token is set
        if self.github_monitor.token:
            self.github_monitor.stop_monitoring()
            self.github_monitor.start_monitoring()
    
    def show_projects(self):
        """Show the GitHub projects dialog."""
        dialog = GitHubProjectsDialog(self.github_manager, self)
        dialog.exec_()
    
    def toggle_notifications_panel(self):
        """Toggle the notifications panel."""
        if self.notifications_panel.isVisible():
            self.notifications_panel.hide()
        else:
            # Position panel below GitHub button
            if self.github_button:
                global_pos = self.github_button.mapToGlobal(self.github_button.rect().bottomLeft())
                self.notifications_panel.move(global_pos)
                self.notifications_panel.show()
    
    def on_notification_added(self, notification):
        """
        Handle a new notification.
        
        Args:
            notification (GitHubNotification): The notification to add
        """
        # Add to notifications panel
        self.notifications_panel.add_notification(notification)
        
        # Update badge
        self.update_notification_badge()
    
    def on_project_added(self, project):
        """
        Handle a new project being added.
        
        Args:
            project (GitHubProject): The project that was added
        """
        # Add project to toolbar if it has a toolbar
        if self.toolbar and hasattr(self.toolbar, 'add_project_widget'):
            project_widget = ProjectWidget(project, self.github_manager)
            self.toolbar.add_project_widget(project_widget)
            self.github_manager.project_widgets[project.full_name] = project_widget
    
    def on_project_removed(self, project):
        """
        Handle a project being removed.
        
        Args:
            project (GitHubProject): The project that was removed
        """
        # Remove project from toolbar if it has a toolbar
        if self.toolbar and project.full_name in self.github_manager.project_widgets:
            project_widget = self.github_manager.project_widgets[project.full_name]
            self.toolbar.remove_widget(project_widget)
    
    def update_notification_badge(self):
        """Update the notification badge with the current count."""
        # Count unread notifications
        count = 0
        for widget in self.github_manager.notification_widgets:
            if not widget.notification.read:
                count += 1
        
        # Update badge
        if count > 0:
            self.notification_badge.setText(str(count))
            self.notification_badge.show()
        else:
            self.notification_badge.hide()
    
    def clear_all_notifications(self):
        """Clear all notifications."""
        self.notifications_panel.clear_all_notifications()
        self.update_notification_badge()
