"""
GitHub notification model.
This module provides the GitHubNotification class for representing GitHub notifications.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, Union


class GitHubNotification:
    """
    Represents a GitHub notification (PR, branch, issue, etc.).
    
    This class provides a unified model for GitHub notifications across the application.
    It supports serialization/deserialization for persistence and includes metadata
    such as read status and notification type.
    """
    
    def __init__(
        self,
        title: str,
        url: str,
        created_at: Union[datetime, str],
        type_str: str,
        repo_name: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a GitHub notification.
        
        Args:
            title: Notification title
            url: URL to the PR, branch, issue, etc.
            created_at: When the notification was created (datetime or ISO format string)
            type_str: Type of notification ("pr", "branch", "issue", "push", etc.)
            repo_name: Repository name (optional)
            payload: Raw payload data for additional context (optional)
        """
        self.title = title
        self.url = url
        
        # Handle created_at as either datetime or string
        if isinstance(created_at, str):
            try:
                self.created_at = datetime.fromisoformat(created_at)
            except ValueError:
                self.created_at = datetime.now()
        else:
            self.created_at = created_at
            
        self.type = type_str
        self.repo_name = repo_name
        self.payload = payload or {}
        self.read = False
    
    def mark_as_read(self) -> None:
        """Mark the notification as read."""
        self.read = True
    
    def mark_as_unread(self) -> None:
        """Mark the notification as unread."""
        self.read = False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert notification to dictionary for serialization.
        
        Returns:
            Dictionary representation of the notification
        """
        return {
            'title': self.title,
            'url': self.url,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'type': self.type,
            'repo_name': self.repo_name,
            'payload': self.payload,
            'read': self.read
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubNotification':
        """
        Create notification from dictionary.
        
        Args:
            data: Dictionary representation of a notification
            
        Returns:
            GitHubNotification instance
        """
        notification = cls(
            title=data.get('title', ''),
            url=data.get('url', ''),
            created_at=data.get('created_at', datetime.now()),
            type_str=data.get('type', ''),
            repo_name=data.get('repo_name'),
            payload=data.get('payload', {})
        )
        notification.read = data.get('read', False)
        return notification
    
    def __str__(self) -> str:
        """String representation of the notification."""
        return f"{self.title} ({self.type})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the notification."""
        return f"GitHubNotification(title='{self.title}', type='{self.type}', read={self.read})"
