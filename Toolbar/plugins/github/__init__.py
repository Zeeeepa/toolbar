"""
GitHub integration plugin for the Toolbar application.
"""

import os
import logging
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget

logger = logging.getLogger(__name__)

class GitHubPlugin:
    def __init__(self):
        self._name = "GitHub Integration"
        self._version = "1.0.0"
        self._description = "GitHub integration plugin"
        self._config = None
        self._event_bus = None
        self._toolbar = None
        self._active = False

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def description(self):
        return self._description

    def initialize(self, config, event_bus, toolbar):
        self._config = config
        self._event_bus = event_bus
        self._toolbar = toolbar
        self._active = True

    def is_active(self):
        return self._active

    def get_icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icons/github.png")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        return None

    def get_actions(self):
        return [
            {
                "name": "Open GitHub",
                "callback": self.open_github
            },
            {
                "name": "View PRs",
                "callback": self.view_prs
            }
        ]

    def handle_click(self):
        self.open_github()

    def open_github(self):
        # Open GitHub in browser
        pass

    def view_prs(self):
        # View pull requests
        pass

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from ...core.enhanced_plugin_system import EnhancedPlugin

class GitHubPlugin(EnhancedPlugin):
    def __init__(self):
        super().__init__()
        self.name = "GitHub Integration"
        self.description = "GitHub repository integration"
        self.version = "1.0.0"
        self.icon = "Toolbar/assets/github.png"
        self.repositories = []
        
    def initialize(self, config):
        """Initialize the plugin"""
        self.config = config
        self.load_repositories()
        
    def get_name(self):
        """Get plugin name"""
        return self.name
        
    def get_description(self):
        """Get plugin description"""
        return self.description
        
    def get_version(self):
        """Get plugin version"""
        return self.version
        
    def get_icon(self):
        """Get plugin icon"""
        return self.icon
        
    def get_actions(self):
        """Get plugin actions"""
        return [
            {
                "name": "Add Repository",
                "callback": self.show_manager,
                "icon": "Toolbar/assets/add.png"
            },
            {
                "name": "View Repositories",
                "callback": self.show_repositories,
                "icon": "Toolbar/assets/view.png"
            }
        ]
        
    def load_repositories(self):
        """Load repositories from config"""
        try:
            if self.config and "github" in self.config:
                self.repositories = self.config["github"].get("repositories", [])
        except Exception as e:
            self.logger.error(f"Error loading repositories: {str(e)}")
            self.logger.error(f"{str(e)}", exc_info=True)
            
    def save_repositories(self):
        """Save repositories to config"""
        try:
            if not self.config:
                self.config = {}
            if "github" not in self.config:
                self.config["github"] = {}
            self.config["github"]["repositories"] = self.repositories
            self.config.save()
        except Exception as e:
            self.logger.error(f"Error saving repositories: {str(e)}")
            self.logger.error(f"{str(e)}", exc_info=True)
            
    def show_manager(self):
        """Show repository manager dialog"""
        try:
            dialog = RepositoryManagerDialog(self)
            dialog.exec_()
        except Exception as e:
            self.logger.error(f"Error showing repository manager: {str(e)}")
            self.logger.error(f"{str(e)}", exc_info=True)
            
    def show_repositories(self):
        """Show repositories dialog"""
        try:
            dialog = RepositoryListDialog(self)
            dialog.exec_()
        except Exception as e:
            self.logger.error(f"Error showing repositories: {str(e)}")
            self.logger.error(f"{str(e)}", exc_info=True)
            
class RepositoryManagerDialog(QDialog):
    def __init__(self, plugin):
        super().__init__()
        self.plugin = plugin
        self.init_ui()
        
    def init_ui(self):
        """Initialize dialog UI"""
        # Set window properties
        self.setWindowTitle("GitHub Repository Manager")
        self.setWindowIcon(QIcon(self.plugin.get_icon()))
        self.setFixedSize(400, 500)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Add title
        title = QLabel("Select repositories to add:")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)
        
        # Add repository list
        self.repo_list = QListWidget()
        self.repo_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.repo_list)
        
        # Add buttons
        add_btn = QPushButton("Add Selected")
        add_btn.clicked.connect(self.add_repositories)
        layout.addWidget(add_btn)
        
        # Load repositories
        self.load_repositories()
        
    def load_repositories(self):
        """Load available repositories"""
        try:
            # TODO: Load repositories from GitHub API
            repos = [
                "repo1",
                "repo2",
                "repo3"
            ]
            
            for repo in repos:
                self.repo_list.addItem(repo)
                
        except Exception as e:
            self.plugin.logger.error(f"Error loading repositories: {str(e)}")
            self.plugin.logger.error(f"{str(e)}", exc_info=True)
            
    def add_repositories(self):
        """Add selected repositories"""
        try:
            selected = self.repo_list.selectedItems()
            for item in selected:
                repo = item.text()
                if repo not in self.plugin.repositories:
                    self.plugin.repositories.append(repo)
            
            self.plugin.save_repositories()
            self.accept()
            
        except Exception as e:
            self.plugin.logger.error(f"Error adding repositories: {str(e)}")
            self.plugin.logger.error(f"{str(e)}", exc_info=True)
            
class RepositoryListDialog(QDialog):
    def __init__(self, plugin):
        super().__init__()
        self.plugin = plugin
        self.init_ui()
        
    def init_ui(self):
        """Initialize dialog UI"""
        # Set window properties
        self.setWindowTitle("GitHub Repositories")
        self.setWindowIcon(QIcon(self.plugin.get_icon()))
        self.setFixedSize(400, 500)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Add title
        title = QLabel("Added repositories:")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)
        
        # Add repository list
        repo_list = QListWidget()
        layout.addWidget(repo_list)
        
        # Load repositories
        for repo in self.plugin.repositories:
            repo_list.addItem(repo)
            
        # Add close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
