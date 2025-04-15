"""
GitHub integration plugin for the Toolbar application.
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal

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
        
        return True
    
    def get_icon(self):
        """Get the icon for the plugin to display in the taskbar."""
        from PyQt5.QtGui import QIcon
        return QIcon.fromTheme("github")
    
    def get_title(self):
        """Get the title for the plugin to display in the taskbar."""
        return "GitHub"
    
    def activate(self):
        """Activate the plugin when its taskbar button is clicked."""
        if not self.github_ui:
            try:
                from Toolbar.plugins.github.ui.github_ui import GitHubUI
                from Toolbar.main import get_toolbar_instance
                toolbar = get_toolbar_instance()
                if toolbar:
                    self.github_ui = GitHubUI(self.github_manager, toolbar)
                    self.github_ui.show()
            except Exception as e:
                logger.error(f"Error creating GitHub UI: {e}")
        elif self.github_ui:
            self.github_ui.show()
    
    def cleanup(self):
        """Clean up resources used by the plugin."""
        logger.info("Cleaning up GitHub plugin")
        if self.github_manager:
            self.github_manager.cleanup()
        return True
