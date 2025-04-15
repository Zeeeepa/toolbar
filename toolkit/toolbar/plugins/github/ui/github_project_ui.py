import os
import webbrowser
import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QListWidget, QListWidgetItem, 
                           QWidget, QMenu, QAction, QMessageBox, QLineEdit,
                           QCheckBox, QGroupBox)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QRect

# Configure logging
logger = logging.getLogger(__name__)

class ProjectWidget(QWidget):
    """Widget for displaying a GitHub project with notification badge."""
    
    clicked = pyqtSignal(object)  # Emits the project when clicked
    settings_clicked = pyqtSignal(object)  # Emits the project when settings button is clicked
    
    def __init__(self, project, parent=None):
        """
        Initialize a project widget.
        
        Args:
            project: The project to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.project = project
        self.setMinimumSize(40, 40)
        self.setMaximumSize(40, 40)
        self.setToolTip(f"{project.name} ({project.full_name})")
        
        # Load project icon
        self.icon = self.load_project_icon()
        
        # Set context menu policy
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set cursor to pointing hand
        self.setCursor(Qt.PointingHandCursor)
    
    def load_project_icon(self):
        """Load the project icon from URL or use default."""
        if self.project.icon_url:
            try:
                import requests
                response = requests.get(self.project.icon_url)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    return QIcon(pixmap)
            except Exception as e:
                logger.error(f"Failed to load project icon: {e}")
        
        # Use default icon if failed to load
        return QIcon.fromTheme("folder-github", QIcon.fromTheme("folder"))
    
    def paintEvent(self, event):
        """Custom paint event to draw the icon and notification badge."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw icon
        self.icon.paint(painter, 0, 0, self.width(), self.height())
        
        # Draw notification badge if there are notifications
        if self.project.notifications:
            # Count unread notifications
            unread_count = sum(1 for n in self.project.notifications if not n.read)
            
            if unread_count > 0:
                # Draw red circle for badge
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(255, 0, 0)))
                badge_rect = QRect(self.width() - 16, 0, 16, 16)
                painter.drawEllipse(badge_rect)
                
                # Draw notification count
                painter.setPen(QPen(QColor(255, 255, 255)))
                painter.drawText(badge_rect, Qt.AlignCenter, str(unread_count))
    
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.LeftButton:
            # Emit clicked signal
            self.clicked.emit(self.project)
        
        super().mousePressEvent(event)
    
    def show_context_menu(self, position):
        """Show context menu for the project widget."""
        menu = QMenu()
        
        # Open project action
        open_project_action = menu.addAction("Open Project")
        open_project_action.triggered.connect(lambda: webbrowser.open(self.project.url))
        
        # Settings action
        settings_action = menu.addAction("Project Settings")
        settings_action.triggered.connect(lambda: self.settings_clicked.emit(self.project))
        
        # Notifications submenu
        if self.project.notifications:
            notifications_menu = menu.addMenu(f"Notifications ({len(self.project.notifications)})")
            
            for notification in self.project.notifications:
                action = notifications_menu.addAction(notification.title)
                action.triggered.connect(lambda checked=False, n=notification: self.open_notification(n))
            
            # Clear notifications action
            menu.addSeparator()
            clear_notifications_action = menu.addAction("Clear Notifications")
            clear_notifications_action.triggered.connect(self.clear_notifications)
        
        # Unpin project action
        menu.addSeparator()
        unpin_action = menu.addAction("Unpin Project")
        unpin_action.triggered.connect(self.unpin_project)
        
        menu.exec_(self.mapToGlobal(position))
    
    def open_notification(self, notification):
        """Open a notification in the browser."""
        webbrowser.open(notification.url)
        notification.read = True
        self.update()  # Repaint the widget
    
    def clear_notifications(self):
        """Clear all notifications for this project."""
        self.project.notifications = []
        self.update()  # Repaint the widget
    
    def unpin_project(self):
        """Unpin the project."""
        self.project.pinned = False
        self.parent().remove_project_widget(self)

class ProjectSettingsDialog(QDialog):
    """Dialog for configuring project-specific settings."""
    
    def __init__(self, project, github_monitor, parent=None):
        """
        Initialize the project settings dialog.
        
        Args:
            project: The project to configure
            github_monitor: The GitHub monitor instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.project = project
        self.github_monitor = github_monitor
        self.setWindowTitle(f"Project Settings: {project.name}")
        self.setMinimumSize(400, 300)
        
        # Set up the UI
        self._init_ui()
        
        # Load current settings
        self.load_settings()
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        
        # Project info
        info_layout = QHBoxLayout()
        
        # Project icon
        icon_label = QLabel()
        if self.project.icon_url:
            try:
                import requests
                response = requests.get(self.project.icon_url)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    icon_label.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except Exception as e:
                logger.error(f"Failed to load project icon: {e}")
        
        info_layout.addWidget(icon_label)
        
        # Project details
        details_layout = QVBoxLayout()
        name_label = QLabel(f"<b>{self.project.name}</b>")
        full_name_label = QLabel(self.project.full_name)
        url_label = QLabel(f"<a href='{self.project.url}'>{self.project.url}</a>")
        url_label.setOpenExternalLinks(True)
        
        details_layout.addWidget(name_label)
        details_layout.addWidget(full_name_label)
        details_layout.addWidget(url_label)
        
        info_layout.addLayout(details_layout)
        layout.addLayout(info_layout)
        
        # Notification settings
        notification_group = QGroupBox("Notification Settings")
        notification_layout = QVBoxLayout()
        
        # PR notifications
        self.pr_checkbox = QCheckBox("Show Pull Request notifications")
        notification_layout.addWidget(self.pr_checkbox)
        
        # Branch notifications
        self.branch_checkbox = QCheckBox("Show Branch notifications")
        notification_layout.addWidget(self.branch_checkbox)
        
        notification_group.setLayout(notification_layout)
        layout.addWidget(notification_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        
        clear_button = QPushButton("Clear Notifications")
        clear_button.clicked.connect(self.clear_notifications)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(clear_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_settings(self):
        """Load current project settings."""
        self.pr_checkbox.setChecked(self.project.show_pr_notifications)
        self.branch_checkbox.setChecked(self.project.show_branch_notifications)
    
    def save_settings(self):
        """Save project settings."""
        self.project.show_pr_notifications = self.pr_checkbox.isChecked()
        self.project.show_branch_notifications = self.branch_checkbox.isChecked()
        
        # Save to GitHub monitor
        self.github_monitor.set_project_notification_settings(
            self.project.full_name,
            self.project.show_pr_notifications,
            self.project.show_branch_notifications
        )
        
        QMessageBox.information(self, "Success", "Project settings saved successfully.")
    
    def clear_notifications(self):
        """Clear all notifications for this project."""
        reply = QMessageBox.question(
            self, 
            "Clear Notifications", 
            f"Are you sure you want to clear all notifications for {self.project.name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.github_monitor.clear_project_notifications(self.project.full_name)
            QMessageBox.information(self, "Success", "Notifications cleared successfully.")

class GitHubProjectsDialog(QDialog):
    """Dialog for managing GitHub projects."""
    
    def __init__(self, github_monitor, parent=None):
        """
        Initialize the GitHub projects dialog.
        
        Args:
            github_monitor: The GitHub monitor instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.github_monitor = github_monitor
        self.setWindowTitle("GitHub Projects")
        self.setMinimumSize(700, 500)
        
        # Set up the UI
        self.init_ui()
        
        # Load projects
        self.load_projects()
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Search field
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Filter repositories...")
        self.search_field.textChanged.connect(self.filter_projects)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_field)
        main_layout.addLayout(search_layout)
        
        # Projects list
        self.projects_list = QListWidget()
        self.projects_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.projects_list.setAlternatingRowColors(True)
        
        # Status label
        self.status_label = QLabel("Loading repositories...")
        main_layout.addWidget(self.status_label)
        
        main_layout.addWidget(QLabel("Available Projects:"))
        main_layout.addWidget(self.projects_list)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        main_layout.addLayout(buttons_layout)
        
        self.pin_button = QPushButton("Pin Selected")
        self.pin_button.clicked.connect(self.pin_selected_projects)
        buttons_layout.addWidget(self.pin_button)
        
        self.unpin_button = QPushButton("Unpin Selected")
        self.unpin_button.clicked.connect(self.unpin_selected_projects)
        buttons_layout.addWidget(self.unpin_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_projects)
        buttons_layout.addWidget(self.refresh_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        buttons_layout.addWidget(close_button)
    
    def load_projects(self):
        """Load projects from the GitHub monitor."""
        try:
            self.status_label.setText("Loading repositories...")
            self.refresh_button.setEnabled(False)
            self.projects_list.clear()
            
            # Get all projects
            projects = self.github_monitor.get_projects()
            
            # Sort projects alphabetically by name
            projects.sort(key=lambda p: p.name.lower())
            
            # Add projects to list
            for project in projects:
                item = QListWidgetItem(f"{project.name} ({project.full_name})")
                item.setData(Qt.UserRole, project)
                
                # Set icon
                if project.icon_url:
                    try:
                        import requests
                        response = requests.get(project.icon_url)
                        if response.status_code == 200:
                            pixmap = QPixmap()
                            pixmap.loadFromData(response.content)
                            item.setIcon(QIcon(pixmap))
                    except Exception as e:
                        logger.error(f"Failed to load project icon: {e}")
                
                # Set checkmark for pinned projects
                item.setCheckState(Qt.Checked if project.pinned else Qt.Unchecked)
                
                self.projects_list.addItem(item)
            
            self.status_label.setText(f"Loaded {self.projects_list.count()} repositories")
            self.refresh_button.setEnabled(True)
            
        except Exception as e:
            self.status_label.setText(f"Error loading repositories: {str(e)}")
            logger.error(f"Failed to load projects: {e}")
            self.refresh_button.setEnabled(True)
    
    def filter_projects(self, filter_text):
        """Filter the projects list based on search text."""
        for i in range(self.projects_list.count()):
            item = self.projects_list.item(i)
            if filter_text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def pin_selected_projects(self):
        """Pin selected projects."""
        for item in self.projects_list.selectedItems():
            project = item.data(Qt.UserRole)
            project.pinned = True
            item.setCheckState(Qt.Checked)
            self.github_monitor.pin_project(project.full_name, True)
    
    def unpin_selected_projects(self):
        """Unpin selected projects."""
        for item in self.projects_list.selectedItems():
            project = item.data(Qt.UserRole)
            project.pinned = False
            item.setCheckState(Qt.Unchecked)
            self.github_monitor.pin_project(project.full_name, False)
    
    def refresh_projects(self):
        """Refresh the projects list."""
        try:
            # Disable button while refreshing
            self.refresh_button.setEnabled(False)
            self.status_label.setText("Refreshing repositories...")
            
            # Check GitHub for updates in a non-blocking way using QTimer
            def do_check():
                try:
                    # Perform GitHub check
                    self.github_monitor.check_github_updates(send_notifications=False)
                    
                    # Then reload projects
                    self.load_projects()
                except Exception as e:
                    self.status_label.setText(f"Error refreshing: {str(e)}")
                    logger.error(f"Error refreshing projects: {e}")
                    self.refresh_button.setEnabled(True)
            
            # Use single shot timer with 100ms delay to make UI responsive
            QTimer.singleShot(100, do_check)
            
        except Exception as e:
            self.status_label.setText(f"Error initializing refresh: {str(e)}")
            logger.error(f"Failed to refresh projects: {e}")
            self.refresh_button.setEnabled(True)
