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
from Toolbar.core.plugin_system import Plugin, PluginType

logger = logging.getLogger(__name__)

class GitHubPlugin(Plugin):
    """Plugin for GitHub integration."""
    
    def __init__(self):
        """Initialize the GitHub plugin."""
        super().__init__()
        self._name = "GitHub Integration"
        self._version = "1.0.0"
        self._description = "GitHub integration and notifications"
        self._icon = None
        self.github_manager = None
        self.github_ui = None
        self.toolbar_button = None
        
    def initialize(self, config, event_bus=None, toolbar=None):
        """
        Initialize the GitHub plugin.
        
        Args:
            config: Configuration object
            event_bus: Event bus object
            toolbar: Toolbar object
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
    
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    def get_icon(self):
        if not self._icon:
            # Return QIcon object instead of string path
            self._icon = QIcon.fromTheme("github")
        return self._icon
    
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
