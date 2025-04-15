import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

class GitHubNotification:
    """
    Represents a GitHub notification (PR or branch).
    """
    def __init__(self, title, url, created_at, type_str, repo_name=None, payload=None):
        """
        Initialize a GitHub notification.
        
        Args:
            title (str): Notification title
            url (str): URL to the PR or branch
            created_at (datetime): When the notification was created
            type_str (str): Type of notification ("pr", "branch", "push", etc.)
            repo_name (str, optional): Repository name
            payload (dict, optional): Raw payload data for additional context
        """
        self.title = title
        self.url = url
        self.created_at = created_at
        self.type = type_str
        self.repo_name = repo_name
        self.payload = payload

class GitHubProject:
    """
    Represents a GitHub project/repository.
    """
    def __init__(self, name, full_name, owner, url, icon_url=None):
        """
        Initialize a GitHub project.
        
        Args:
            name (str): Project name
            full_name (str): Full repository name (owner/repo)
            owner (str): Repository owner
            url (str): Repository URL
            icon_url (str, optional): URL to repository icon
        """
        self.name = name
        self.full_name = full_name
        self.owner = owner
        self.url = url
        self.icon_url = icon_url
        self.notifications = []
        self.pinned = False
    
    def add_notification(self, notification):
        """Add a notification to this project."""
        self.notifications.append(notification) 