"""
GitHub integration plugin for the Toolbar application.
"""

import os
import logging
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon

# Import from local modules
from Toolbar.plugins.github.github.monitor import GitHubMonitor
from Toolbar.plugins.github.github_manager import GitHubManager
from Toolbar.plugins.github.github.models import GitHubProject, GitHubNotification
from Toolbar.core.plugin_system import Plugin

logger = logging.getLogger(__name__)

class GitHubPlugin(Plugin):
    """GitHub integration plugin for the Toolbar application."""
    
    def __init__(self):
        """Initialize the GitHub plugin."""
        super().__init__()
        self.name = "GitHub Integration"
        self.description = "Integrates with GitHub to monitor repositories and provide notifications."
        self.version = "1.0.0"
        self.github_manager = None
        self.github_ui = None
        self.toolbar_button = None
        
    def initialize(self, config):
        """
        Initialize the GitHub plugin.
        
        Args:
            config: Configuration object
        """
        logger.info("Initializing GitHub plugin")
        
        # Create GitHub monitor
        github_monitor = GitHubMonitor(config)
        
        # Create GitHub manager
        self.github_manager = GitHubManager(github_monitor)
        
        # Create GitHub UI
        try:
            from Toolbar.plugins.github.ui.github_ui import GitHubUI
            from Toolbar.main import get_toolbar_instance
            toolbar = get_toolbar_instance()
            if toolbar:
                self.github_ui = GitHubUI(self.github_manager.github_monitor, toolbar)
                
                # Add GitHub button to the left side of the toolbar
                if hasattr(toolbar, 'toolbar'):
                    # Create GitHub button
                    self.toolbar_button = self.github_ui.github_button
                    
                    # Add button to the left side of the toolbar
                    toolbar.toolbar.insertWidget(0, self.toolbar_button)
                    
                    # Add notification badge next to the button
                    toolbar.toolbar.insertWidget(1, self.github_ui.notification_badge)
                    
                    # Connect button click to show GitHub dialog
                    self.toolbar_button.clicked.connect(self.github_ui.show_github_dialog)
                    
                    logger.info("GitHub button added to toolbar")
        except Exception as e:
            logger.error(f"Error creating GitHub UI: {e}")
        
        return True
    
    def get_icon(self):
        """Get the icon for the plugin to display in the taskbar."""
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "github.svg")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        return QIcon.fromTheme("github")
    
    def get_title(self):
        """Get the title for the plugin to display in the taskbar."""
        return "GitHub"
    
    def activate(self):
        """Activate the plugin when its taskbar button is clicked."""
        if self.github_ui:
            self.github_ui.show_github_dialog()
    
    def cleanup(self):
        """Clean up resources used by the plugin."""
        logger.info("Cleaning up GitHub plugin")
        if self.github_manager:
            self.github_manager.cleanup()
        return True
