"""
GitHub integration module.
This module provides tools for monitoring GitHub repositories,
handling webhooks, and managing notifications.
"""

# Import from local modules
from Toolbar.core.github.models import GitHubProject, GitHubNotification
from Toolbar.core.github.ngrok_manager import NgrokManager
from Toolbar.core.github.webhook_handler import WebhookHandler
from Toolbar.core.github.webhook_manager import WebhookManager
from Toolbar.core.github.monitor import GitHubMonitor

# Export all the necessary classes
__all__ = [
    'GitHubMonitor',
    'GitHubProject', 
    'GitHubNotification',
    'WebhookManager', 
    'NgrokManager', 
    'WebhookHandler'
]
