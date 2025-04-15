"""
GitHub integration module.
This module provides tools for monitoring GitHub repositories,
handling webhooks, and managing notifications.
"""

# Import from the new plugin-based structure
from Toolbar.plugins.github.github.models import GitHubProject, GitHubNotification
from Toolbar.plugins.github.github.ngrok_manager import NgrokManager
from Toolbar.plugins.github.github.webhook_handler import WebhookHandler
from Toolbar.plugins.github.github.webhook_manager import WebhookManager
from Toolbar.plugins.github.github.monitor import GitHubMonitor

# Export all the necessary classes
__all__ = [
    'GitHubMonitor',
    'GitHubProject', 
    'GitHubNotification',
    'WebhookManager', 
    'NgrokManager', 
    'WebhookHandler'
]
