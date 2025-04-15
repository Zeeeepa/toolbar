"""
GitHub project model.
This module provides the GitHubProject class for representing GitHub repositories.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from toolkit.models.github.notification import GitHubNotification


class GitHubProject:
    """
    Represents a GitHub project/repository.
    
    This class provides a unified model for GitHub repositories across the application.
    It supports serialization/deserialization for persistence and includes metadata
    such as pinned status and notifications.
    """
    
    def __init__(
        self,
        name: str,
        full_name: str,
        owner: str,
        url: str,
        icon_url: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Initialize a GitHub project.
        
        Args:
            name: Project name
            full_name: Full repository name (owner/repo)
            owner: Repository owner
            url: Repository URL
            icon_url: URL to repository icon (optional)
            description: Repository description (optional)
        """
        self.name = name
        self.full_name = full_name
        self.owner = owner
        self.url = url
        self.icon_url = icon_url
        self.description = description
        self.notifications: List[GitHubNotification] = []
        self.pinned = False
        self.last_updated = datetime.now()
    
    def add_notification(self, notification: GitHubNotification) -> None:
        """
        Add a notification to this project.
        
        Args:
            notification: The notification to add
        """
        self.notifications.append(notification)
        self.last_updated = datetime.now()
    
    def clear_notifications(self) -> None:
        """Clear all notifications for this project."""
        self.notifications = []
    
    def get_unread_notifications(self) -> List[GitHubNotification]:
        """
        Get all unread notifications for this project.
        
        Returns:
            List of unread notifications
        """
        return [n for n in self.notifications if not n.read]
    
    def mark_all_as_read(self) -> None:
        """Mark all notifications as read."""
        for notification in self.notifications:
            notification.mark_as_read()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert project to dictionary for serialization.
        
        Returns:
            Dictionary representation of the project
        """
        return {
            'name': self.name,
            'full_name': self.full_name,
            'owner': self.owner,
            'url': self.url,
            'icon_url': self.icon_url,
            'description': self.description,
            'pinned': self.pinned,
            'last_updated': self.last_updated.isoformat() if isinstance(self.last_updated, datetime) else self.last_updated,
            'notifications': [n.to_dict() for n in self.notifications]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubProject':
        """
        Create project from dictionary.
        
        Args:
            data: Dictionary representation of a project
            
        Returns:
            GitHubProject instance
        """
        project = cls(
            name=data.get('name', ''),
            full_name=data.get('full_name', ''),
            owner=data.get('owner', ''),
            url=data.get('url', ''),
            icon_url=data.get('icon_url'),
            description=data.get('description')
        )
        project.pinned = data.get('pinned', False)
        
        # Parse last_updated
        last_updated = data.get('last_updated')
        if isinstance(last_updated, str):
            try:
                project.last_updated = datetime.fromisoformat(last_updated)
            except ValueError:
                project.last_updated = datetime.now()
        elif last_updated:
            project.last_updated = last_updated
        
        # Load notifications
        for notification_data in data.get('notifications', []):
            project.notifications.append(GitHubNotification.from_dict(notification_data))
        
        return project
    
    def __str__(self) -> str:
        """String representation of the project."""
        return f"{self.name} ({self.full_name})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the project."""
        return f"GitHubProject(name='{self.name}', full_name='{self.full_name}', pinned={self.pinned})"
