"""
GitHub integration module.
This module provides tools for monitoring GitHub repositories,
handling webhooks, and managing notifications.
"""

# First import the models that have no dependencies
from Toolbar.core.github.models import GitHubProject, GitHubNotification

# Then import the webhook components
from Toolbar.core.github.ngrok_manager import NgrokManager
from Toolbar.core.github.webhook_handler import WebhookHandler
from Toolbar.core.github.webhook_manager import WebhookManager

# Finally import the monitor that depends on all of the above
from Toolbar.core.github.monitor import GitHubMonitor

__all__ = [
    'GitHubMonitor',
    'GitHubProject', 
    'GitHubNotification',
    'WebhookManager', 
    'NgrokManager', 
    'WebhookHandler'
] 