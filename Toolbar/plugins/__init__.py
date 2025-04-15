"""
Plugin package for the Toolbar application.
This package contains all the plugins that extend the toolbar's functionality.
"""

# Import plugin classes to make them available
from Toolbar.plugins.github import GitHubPlugin
from Toolbar.plugins.linear import LinearPlugin

__all__ = [
    'GitHubPlugin',
    'LinearPlugin'
]
