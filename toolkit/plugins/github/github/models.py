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
        self.read = False
    
    def mark_as_read(self):
        """Mark the notification as read."""
        self.read = True
    
    def to_dict(self):
        """Convert notification to dictionary for serialization."""
        return {
            'title': self.title,
            'url': self.url,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'type': self.type,
            'repo_name': self.repo_name,
            'read': self.read
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create notification from dictionary."""
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = datetime.now()
        
        notification = cls(
            title=data.get('title', ''),
            url=data.get('url', ''),
            created_at=created_at,
            type_str=data.get('type', ''),
            repo_name=data.get('repo_name')
        )
        notification.read = data.get('read', False)
        return notification

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
    
    def clear_notifications(self):
        """Clear all notifications for this project."""
        self.notifications = []
    
    def to_dict(self):
        """Convert project to dictionary for serialization."""
        return {
            'name': self.name,
            'full_name': self.full_name,
            'owner': self.owner,
            'url': self.url,
            'icon_url': self.icon_url,
            'pinned': self.pinned,
            'notifications': [n.to_dict() for n in self.notifications]
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create project from dictionary."""
        project = cls(
            name=data.get('name', ''),
            full_name=data.get('full_name', ''),
            owner=data.get('owner', ''),
            url=data.get('url', ''),
            icon_url=data.get('icon_url')
        )
        project.pinned = data.get('pinned', False)
        
        # Load notifications
        for notification_data in data.get('notifications', []):
            project.notifications.append(GitHubNotification.from_dict(notification_data))
        
        return project
