"""
GitHub module initialization.
This module provides GitHub integration functionality.
"""

from toolkit.plugins.github.github.models import GitHubProject, GitHubNotification
from toolkit.plugins.github.github.monitor import GitHubMonitor

__all__ = ['GitHubProject', 'GitHubNotification', 'GitHubMonitor']
