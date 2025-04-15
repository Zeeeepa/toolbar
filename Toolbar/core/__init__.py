"""
Compatibility layer for old import paths.
This module redirects imports from the old structure to the new plugin-based system.
"""

# Import plugin classes to make them available through the old import paths
from Toolbar.plugins.github import GitHubPlugin
from Toolbar.plugins.linear import LinearPlugin

# Create alias for backwards compatibility
class GitHubIntegration:
    """
    Compatibility class for old code that imports GitHubIntegration.
    Redirects to the GitHubPlugin class from the plugin system.
    """
    @staticmethod
    def get_instance(*args, **kwargs):
        """Get a GitHub plugin instance."""
        # Import here to avoid circular imports
        from Toolbar.core.plugin_system import PluginManager
        
        # Try to get the plugin manager from the main module
        try:
            from Toolbar.main import plugin_manager
            if plugin_manager:
                github_plugin = plugin_manager.get_plugin("GitHub Integration")
                if github_plugin:
                    return github_plugin
        except (ImportError, AttributeError):
            pass
        
        # If that fails, create a new instance
        from Toolbar.plugins.github import GitHubPlugin
        return GitHubPlugin()

# Create alias for Linear integration
class LinearIntegration:
    """
    Compatibility class for old code that imports LinearIntegration.
    Redirects to the LinearPlugin class from the plugin system.
    """
    def __new__(cls, *args, **kwargs):
        """Create a new LinearIntegration instance."""
        # Import here to avoid circular imports
        from Toolbar.plugins.linear.linear_integration import LinearIntegration as LinearIntegrationImpl
        return LinearIntegrationImpl(*args, **kwargs)
