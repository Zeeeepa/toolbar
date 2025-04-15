"""
GitHub integration plugin for the Toolbar application.
"""

import logging
from PyQt5.QtWidgets import QWidget

from toolkit.toolbar.core.plugin import Plugin
from .github.monitor import GitHubMonitor
from .ui.github_ui import GitHubUI

# Configure logging
logger = logging.getLogger(__name__)

class GitHubPlugin(Plugin):
    """GitHub integration plugin for the taskbar."""
    
    def __init__(self):
        """Initialize the GitHub plugin."""
        super().__init__()
        self.monitor = None
        self.ui = None
    
    def initialize(self, config):
        """
        Initialize the GitHub plugin.
        
        Args:
            config: Configuration object
        """
        try:
            # Initialize GitHub monitor
            self.monitor = GitHubMonitor(config)
            
            # Initialize UI component
            self.ui = GitHubUI(self.monitor)
            
            logger.info("GitHub plugin initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize GitHub plugin: {e}")
            return False
    
    def cleanup(self):
        """Clean up GitHub plugin resources."""
        if self.monitor:
            self.monitor.stop_monitoring()
    
    def get_ui(self):
        """
        Get the UI component for the plugin.
        
        Returns:
            QWidget: The UI component
        """
        return self.ui
    
    @property
    def name(self) -> str:
        """Get the plugin name."""
        return "GitHub Integration"
    
    @property
    def version(self) -> str:
        """Get the plugin version."""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Get the plugin description."""
        return "Provides GitHub repository monitoring and notification functionality in the taskbar."
    
    @property
    def author(self) -> str:
        """Get the plugin author."""
        return "Codegen"
    
    @property
    def icon(self) -> str:
        """Get the plugin icon."""
        return "github"
