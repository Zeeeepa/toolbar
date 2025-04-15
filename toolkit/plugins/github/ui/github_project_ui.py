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
            border-radius: 10px;
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
        else:
            return QIcon.fromTheme("github", QIcon.fromTheme("web-browser"))
    
    def open_project(self):
        """Open the project URL in a web browser."""
        try:
            webbrowser.open(self.project.url)
        except Exception as e:
            logger.error(f"Failed to open project URL: {e}")
    
    def show_context_menu(self, pos):
        """Show the context menu for the project."""
        menu = QMenu()
        
        # Open action
        open_action = menu.addAction("Open in Browser")
        open_action.triggered.connect(self.open_project)
        
        # Separator
        menu.addSeparator()
        
        # Remove action
        remove_action = menu.addAction("Remove from Toolbar")
        remove_action.triggered.connect(self.remove_from_toolbar)
        
        # Clear notifications action
        if self.project.notifications:
            clear_action = menu.addAction("Clear Notifications")
            clear_action.triggered.connect(self.clear_notifications)
        
        # Show menu
        menu.exec_(self.mapToGlobal(pos))
    
    def remove_from_toolbar(self):
        """Remove the project from the toolbar."""
        self.github_manager.remove_project_widget(self)
    
    def clear_notifications(self):
        """Clear all notifications for this project."""
        self.github_manager.clear_project_notifications(self.project)
        self.update_notification_badge()
    
    def update_notification_badge(self):
        """Update the notification badge."""
        # Count unread notifications
        count = len([n for n in self.project.notifications if not n.read])
        
        # Update badge
        if count > 0:
            self.notification_badge.setText(str(count))
            self.notification_badge.show()
            
            # Position badge
            self.notification_badge.setParent(self)
            self.notification_badge.move(
                self.icon_button.x() + self.icon_button.width() - 10,
                self.icon_button.y() - 5
            )
            self.notification_badge.raise_()
        else:
            self.notification_badge.hide()

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
        self.setMinimumSize(500, 400)
        
        # Set up the UI
        self._init_ui()
        
        # Load projects
        self.load_projects()
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Select projects to pin to the toolbar:")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(header_label)
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_projects)
        header_layout.addWidget(refresh_button)
        
        layout.addLayout(header_layout)
        
        # Projects list
        self.projects_list = QListWidget()
        self.projects_list.setAlternatingRowColors(True)
        layout.addWidget(self.projects_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_projects)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def load_projects(self):
        """Load projects from GitHub."""
        self.projects_list.clear()
        
        # Get repositories
        repositories = self.github_manager.get_user_repositories()
        
        # Add to list
        for project in repositories:
            item = QListWidgetItem(project.full_name)
            item.setData(Qt.UserRole, project)
            
            # Create checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(project.pinned)
            
            # Add to list
            self.projects_list.addItem(item)
            self.projects_list.setItemWidget(item, checkbox)
    
    def save_projects(self):
        """Save selected projects."""
        try:
            # Update pinned status for all projects
            for i in range(self.projects_list.count()):
                item = self.projects_list.item(i)
                project = item.data(Qt.UserRole)
                checkbox = self.projects_list.itemWidget(item)
                
                # Update pinned status
                pinned = checkbox.isChecked()
                if pinned != project.pinned:
                    self.github_manager.pin_project(project, pinned)
            
            self.accept()
        
        except Exception as e:
            logger.error(f"Failed to save projects: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Failed to save projects: {e}")
