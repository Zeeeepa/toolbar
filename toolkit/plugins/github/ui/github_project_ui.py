"""
GitHub Project UI module.
This module provides UI components for GitHub projects.
"""

import os
import logging
import webbrowser
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QToolButton, QMenu, QAction,
                           QDialog, QScrollArea, QFrame, QListWidget,
                           QListWidgetItem, QSizePolicy, QCheckBox)
from PyQt5.QtGui import QIcon, QCursor, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QSize

logger = logging.getLogger(__name__)

class ProjectWidget(QWidget):
    """Widget for displaying a GitHub project in the toolbar."""
    
    def __init__(self, project, github_manager, parent=None):
        """
        Initialize a project widget.
        
        Args:
            project (GitHubProject): The project to display
            github_manager (GitHubManager): The GitHub manager instance
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.project = project
        self.github_manager = github_manager
        
        # Set up the UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Project icon
        self.icon_button = QToolButton()
        self.icon_button.setIcon(self._get_project_icon())
        self.icon_button.setIconSize(QSize(32, 32))
        self.icon_button.setToolTip(project.full_name)
        self.icon_button.clicked.connect(self.open_project)
        layout.addWidget(self.icon_button, 0, Qt.AlignCenter)
        
        # Project name
        name_label = QLabel(project.name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setMaximumWidth(80)
        layout.addWidget(name_label, 0, Qt.AlignCenter)
        
        # Notification badge
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
        
        # Add badge to icon button
        self.icon_button.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 2px;
            }
        """)
        
        # Set widget properties
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Update notification badge
        self.update_notification_badge()
    
    def _get_project_icon(self):
        """Get the project icon."""
        # Try to load icon from URL
        if self.project.icon_url:
            try:
                import requests
                from PyQt5.QtGui import QPixmap
                
                response = requests.get(self.project.icon_url)
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                
                return QIcon(pixmap)
            
            except Exception as e:
                logger.error(f"Failed to load project icon: {e}")
        
        # Fallback icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "ui", "icons", "github.svg")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        
        # Default icon
        return QIcon.fromTheme("github", QIcon.fromTheme("web-browser"))
    
    def open_project(self):
        """Open the project in a web browser."""
        webbrowser.open(self.project.url)
    
    def update_notification_badge(self):
        """Update the notification badge with the current count."""
        count = len(self.project.notifications)
        
        if count > 0:
            self.notification_badge.setText(str(count))
            self.notification_badge.show()
        else:
            self.notification_badge.hide()
    
    def show_context_menu(self, position):
        """Show the context menu for the project widget."""
        menu = QMenu()
        
        # Open action
        open_action = QAction("Open in Browser", self)
        open_action.triggered.connect(self.open_project)
        menu.addAction(open_action)
        
        # Notifications action
        if self.project.notifications:
            notifications_menu = QMenu("Notifications", menu)
            
            for notification in self.project.notifications:
                action = QAction(notification.title, self)
                action.triggered.connect(lambda checked=False, url=notification.url: webbrowser.open(url))
                notifications_menu.addAction(action)
            
            notifications_menu.addSeparator()
            
            clear_action = QAction("Clear All", self)
            clear_action.triggered.connect(self.clear_notifications)
            notifications_menu.addAction(clear_action)
            
            menu.addMenu(notifications_menu)
        
        # Unpin action
        unpin_action = QAction("Unpin", self)
        unpin_action.triggered.connect(self.unpin_project)
        menu.addAction(unpin_action)
        
        menu.exec_(self.mapToGlobal(position))
    
    def clear_notifications(self):
        """Clear all notifications for this project."""
        self.github_manager.clear_project_notifications(self.project)
        self.update_notification_badge()
    
    def unpin_project(self):
        """Unpin this project."""
        self.github_manager.pin_project(self.project, False)

class GitHubProjectsDialog(QDialog):
    """Dialog for managing GitHub projects."""
    
    def __init__(self, github_manager, parent=None):
        """
        Initialize the GitHub projects dialog.
        
        Args:
            github_manager (GitHubManager): The GitHub manager instance
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.github_manager = github_manager
        self.setWindowTitle("GitHub Projects")
        self.setMinimumSize(600, 400)
        
        # Set up the UI
        self._init_ui()
        
        # Load projects
        self.load_projects()
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Projects list
        self.projects_list = QListWidget()
        self.projects_list.setSelectionMode(QListWidget.NoSelection)
        layout.addWidget(self.projects_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_projects)
        button_layout.addWidget(refresh_button)
        
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def load_projects(self):
        """Load GitHub projects into the list."""
        self.projects_list.clear()
        
        # Get repositories
        repositories = self.github_manager.get_user_repositories()
        
        if not repositories:
            item = QListWidgetItem("No repositories found or not authenticated")
            self.projects_list.addItem(item)
            return
        
        # Add repositories to list
        for project in repositories:
            item = QListWidgetItem()
            self.projects_list.addItem(item)
            
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 5, 5, 5)
            
            # Project icon
            icon_label = QLabel()
            icon = self._get_project_icon(project)
            icon_label.setPixmap(icon.pixmap(24, 24))
            layout.addWidget(icon_label)
            
            # Project name
            name_label = QLabel(f"<b>{project.name}</b> ({project.full_name})")
            layout.addWidget(name_label, 1)
            
            # Pin checkbox
            pin_checkbox = QCheckBox("Pin to Toolbar")
            pin_checkbox.setChecked(project.pinned)
            pin_checkbox.stateChanged.connect(lambda state, p=project: self.toggle_pin(p, state))
            layout.addWidget(pin_checkbox)
            
            # Set item widget
            self.projects_list.setItemWidget(item, widget)
            item.setSizeHint(widget.sizeHint())
    
    def _get_project_icon(self, project):
        """Get the project icon."""
        # Try to load icon from URL
        if project.icon_url:
            try:
                import requests
                from PyQt5.QtGui import QPixmap
                
                response = requests.get(project.icon_url)
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                
                return QIcon(pixmap)
            
            except Exception as e:
                logger.error(f"Failed to load project icon: {e}")
        
        # Fallback icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "ui", "icons", "github.svg")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        
        # Default icon
        return QIcon.fromTheme("github", QIcon.fromTheme("web-browser"))
    
    def toggle_pin(self, project, state):
        """
        Toggle the pin state of a project.
        
        Args:
            project (GitHubProject): The project to toggle
            state (int): The checkbox state
        """
        pinned = state == Qt.Checked
        self.github_manager.pin_project(project, pinned)
