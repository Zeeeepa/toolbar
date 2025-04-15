import os
import warnings
import webbrowser
import requests
from io import BytesIO
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QListWidget, QListWidgetItem, 
                            QWidget, QMenu, QAction, QMessageBox, QLineEdit)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer

# Suppress PyQt5 deprecation warnings
warnings.filterwarnings("ignore", message=".*sipPyTypeDict.*")

class ProjectWidget(QWidget):
    """Widget for displaying a GitHub project with notification badge."""
    
    clicked = pyqtSignal(object)  # Emits the project when clicked
    
    def __init__(self, project, parent=None):
        """
        Initialize a project widget.
        
        Args:
            project (GitHubProject): The project to display
            parent (QWidget, optional): Parent widget
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
                response = requests.get(self.project.icon_url)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    return QIcon(pixmap)
            except Exception as e:
                warnings.warn(f"Failed to load project icon: {e}")
        
        # Use default icon if failed to load
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "icons", "project.svg")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        return QIcon()
    
    def paintEvent(self, event):
        """Custom paint event to draw the icon and notification badge."""
        super().paintEvent(event)
        
        painter = self.icon.paint(self, 0, 0, self.width(), self.height())
        
        # Draw notification badge if there are notifications
        if self.project.notifications:
            # Load notification badge icon
            badge_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                        "icons", "project_notification.svg")
            if os.path.exists(badge_icon_path):
                badge_icon = QIcon(badge_icon_path)
                badge_icon.paint(painter, self.width() - 16, 0, 16, 16)
            
            # Draw notification count
            painter.setPen(Qt.white)
            painter.drawText(self.width() - 16, 0, 16, 16, Qt.AlignCenter, 
                            str(len(self.project.notifications)))
    
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.LeftButton:
            # If there are notifications, open the first one
            if self.project.notifications:
                webbrowser.open(self.project.notifications[0].url)
            else:
                # Otherwise open the project page
                webbrowser.open(self.project.url)
            
            # Emit clicked signal
            self.clicked.emit(self.project)
        
        super().mousePressEvent(event)
    
    def show_context_menu(self, position):
        """Show context menu for the project widget."""
        menu = QMenu()
        
        # Open project action
        open_project_action = menu.addAction("Open Project")
        open_project_action.triggered.connect(lambda: webbrowser.open(self.project.url))
        
        # Notifications submenu
        if self.project.notifications:
            notifications_menu = menu.addMenu(f"Notifications ({len(self.project.notifications)})")
            
            for notification in self.project.notifications:
                action = notifications_menu.addAction(notification.title)
                action.triggered.connect(lambda checked=False, url=notification.url: webbrowser.open(url))
            
            # Clear notifications action
            menu.addSeparator()
            clear_notifications_action = menu.addAction("Clear Notifications")
            clear_notifications_action.triggered.connect(self.clear_notifications)
        
        # Unpin project action
        menu.addSeparator()
        unpin_action = menu.addAction("Unpin Project")
        unpin_action.triggered.connect(self.unpin_project)
        
        menu.exec_(self.mapToGlobal(position))
    
    def clear_notifications(self):
        """Clear all notifications for this project."""
        self.project.notifications = []
        self.update()  # Repaint the widget
    
    def unpin_project(self):
        """Unpin the project."""
        self.project.pinned = False
        self.parent().remove_project_widget(self)
    
    def update_notification_badge(self):
        """Update the notification badge."""
        self.update()  # Repaint the widget

class GitHubProjectsDialog(QDialog):
    """Dialog for managing GitHub projects."""
    
    def __init__(self, github_monitor, parent=None):
        """
        Initialize the GitHub projects dialog.
        
        Args:
            github_monitor (GitHubMonitor): The GitHub monitor instance
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("GitHub Projects")
        self.setMinimumSize(700, 600)
        
        self.github_monitor = github_monitor
        
        # Set up the UI
        self.init_ui()
        
        # Apply a dark theme to the dialog
        self.apply_dark_theme()
        
        # Load projects
        self.load_projects()
    
    def apply_dark_theme(self):
        """Apply a dark theme to the dialog elements."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: #e1e1e1;
            }
            QLabel {
                color: #e1e1e1;
                font-weight: bold;
            }
            QListWidget {
                background-color: #383838;
                color: #e1e1e1;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QListWidget::item {
                color: #e1e1e1;
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0086e8;
            }
            QPushButton:pressed {
                background-color: #005fa3;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #aaaaaa;
            }
            QLineEdit {
                background-color: #383838;
                color: #e1e1e1;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
        """)
    
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
            projects = list(self.github_monitor.get_projects())
            
            # If no projects are loaded, try to force a check
            if len(projects) == 0:
                self.github_monitor._check_github_updates(send_notifications=False)
                projects = list(self.github_monitor.get_projects())
            
            # Sort projects alphabetically by name
            projects.sort(key=lambda p: p.name.lower())
            
            # Add projects to list
            for project in projects:
                item = QListWidgetItem(f"{project.name} ({project.full_name})")
                item.setData(Qt.UserRole, project)
                
                # Set icon
                if project.icon_url:
                    try:
                        response = requests.get(project.icon_url)
                        if response.status_code == 200:
                            pixmap = QPixmap()
                            pixmap.loadFromData(response.content)
                            item.setIcon(QIcon(pixmap))
                    except Exception as e:
                        warnings.warn(f"Failed to load project icon: {e}")
                
                # Set checkmark for pinned projects
                item.setCheckState(Qt.Checked if project.pinned else Qt.Unchecked)
                
                self.projects_list.addItem(item)
            
            self.status_label.setText(f"Loaded {self.projects_list.count()} repositories")
            self.refresh_button.setEnabled(True)
            
        except Exception as e:
            self.status_label.setText(f"Error loading repositories: {str(e)}")
            warnings.warn(f"Failed to load projects: {e}")
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
        
        # Save projects
        self.github_monitor.save_projects()
    
    def unpin_selected_projects(self):
        """Unpin selected projects."""
        for item in self.projects_list.selectedItems():
            project = item.data(Qt.UserRole)
            project.pinned = False
            item.setCheckState(Qt.Unchecked)
        
        # Save projects
        self.github_monitor.save_projects()
    
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
                    self.github_monitor._check_github_updates(send_notifications=False)
                    
                    # Then reload projects
                    self.load_projects()
                except Exception as e:
                    self.status_label.setText(f"Error refreshing: {str(e)}")
                    warnings.warn(f"Error refreshing projects: {e}")
                    self.refresh_button.setEnabled(True)
            
            # Use single shot timer with 100ms delay to make UI responsive
            QTimer.singleShot(100, do_check)
            
        except Exception as e:
            self.status_label.setText(f"Error initializing refresh: {str(e)}")
            warnings.warn(f"Failed to refresh projects: {e}")
            self.refresh_button.setEnabled(True)
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        try:
            # Save projects
            self.github_monitor.save_projects()
        except Exception as e:
            warnings.warn(f"Error saving projects: {e}")
        event.accept()
