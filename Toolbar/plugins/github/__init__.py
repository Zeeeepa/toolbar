"""
GitHub integration plugin for the Toolbar application.
This plugin provides integration with GitHub repositories, allowing users to monitor repositories,
receive notifications for pull requests and branches, and manage GitHub projects.
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal

# Import from core modules
from Toolbar.core.github import GitHubMonitor, GitHubProject, GitHubNotification
from Toolbar.core.github_manager import GitHubManager
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
        
    def initialize(self, config, toolbar=None):
        """
        Initialize the GitHub plugin.
        
        Args:
            config: Configuration object
            toolbar: Toolbar instance
        """
        logger.info("Initializing GitHub plugin")
        
        # Create GitHub monitor
        github_monitor = GitHubMonitor(config)
        
        # Create GitHub manager
        self.github_manager = GitHubManager(github_monitor)
        
        # Create GitHub UI if toolbar is provided
        if toolbar:
            try:
                from Toolbar.plugins.github.ui.github_ui import GitHubUI
                self.github_ui = GitHubUI(self.github_manager, toolbar)
            except Exception as e:
                logger.error(f"Error creating GitHub UI: {e}")
        
        return True
    
    def cleanup(self):
        """Clean up resources used by the plugin."""
        logger.info("Cleaning up GitHub plugin")
        if self.github_manager:
            self.github_manager.cleanup()
        return True
