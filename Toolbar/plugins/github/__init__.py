"""
GitHub integration plugin for the Toolbar application.
"""

from Toolbar.core.plugin_system import Plugin
from Toolbar.core.github.monitor import GitHubMonitor
from Toolbar.core.github_manager import GitHubManager

class GitHubPlugin(Plugin):
    """GitHub integration plugin."""
    
    def __init__(self):
        self.monitor = None
        self.manager = None
    
    def initialize(self, config):
        """Initialize the GitHub plugin."""
        try:
            # Initialize GitHub monitor
            self.monitor = GitHubMonitor(config)
            
            # Initialize GitHub manager
            self.manager = GitHubManager(self.monitor)
            
            # Start monitoring if enabled
            if config.get('github', 'token'):
                self.monitor.start_monitoring()
                
                # Set up webhooks if enabled
                if config.get('github', 'webhook_enabled', False):
                    self.monitor.setup_webhooks()
        except Exception as e:
            print(f"Failed to initialize GitHub plugin: {e}")
    
    def cleanup(self):
        """Clean up GitHub plugin resources."""
        if self.monitor:
            self.monitor.stop_monitoring()
    
    @property
    def name(self) -> str:
        return "GitHub Integration"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Provides GitHub repository monitoring and webhook functionality." 