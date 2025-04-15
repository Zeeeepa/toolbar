"""
GitHub integration plugin for the Toolkit application.
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal

# Import local modules
from toolkit.plugins.github.github.monitor import GitHubMonitor
from toolkit.plugins.github.github_manager import GitHubManager

logger = logging.getLogger(__name__)

class GitHubPlugin(QObject):
    """GitHub integration plugin for Toolkit."""
    
    # Signals
    plugin_loaded = pyqtSignal()
    plugin_unloaded = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor = None
        self.manager = None
        self.ui = None
        self.config = None
        self.toolbar = None
    
    def initialize(self, config, toolbar):
        """
        Initialize the GitHub plugin.
        
        Args:
            config: Configuration object
            toolbar: Toolbar object
        """
        try:
            logger.info("Initializing GitHub plugin")
            self.config = config
            self.toolbar = toolbar
            
            # Initialize GitHub monitor
            self.monitor = GitHubMonitor(config)
            
            # Initialize GitHub manager
            self.manager = GitHubManager(self.monitor)
            
            # Initialize UI
            from toolkit.plugins.github.ui.github_ui import GitHubUI
            self.ui = GitHubUI(self.manager, toolbar)
            
            # Add GitHub icon to the middle of toolbar
            self.ui.add_to_toolbar(position='middle')
            
            # Start monitoring if enabled
            if config.get('github', 'token', ''):
                self.monitor.start_monitoring()
            
            # Emit signal
            self.plugin_loaded.emit()
            
            logger.info("GitHub plugin initialized")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize GitHub plugin: {e}")
            return False
    
    def cleanup(self):
        """Clean up GitHub plugin resources."""
        try:
            logger.info("Cleaning up GitHub plugin")
            
            # Stop monitoring
            if self.monitor:
                self.monitor.stop_monitoring()
            
            # Remove UI elements
            if self.ui:
                self.ui.remove_from_toolbar()
            
            # Emit signal
            self.plugin_unloaded.emit()
            
            logger.info("GitHub plugin cleaned up")
            return True
        
        except Exception as e:
            logger.error(f"Failed to clean up GitHub plugin: {e}")
            return False
    
    @property
    def name(self) -> str:
        return "GitHub Integration"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Provides GitHub repository monitoring and notification functionality."
    
    @property
    def author(self) -> str:
        return "Toolkit Team"
    
    @property
    def icon_path(self) -> str:
        return "github/ui/icons/github.svg"
