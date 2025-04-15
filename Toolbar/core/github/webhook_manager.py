import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

class WebhookManager:
    """
    Manages GitHub webhooks for repositories.
    """
    
    def __init__(self, token: str, webhook_url: str, secret: Optional[str] = None):
        """
        Initialize the webhook manager.
        
        Args:
            token (str): GitHub API token
            webhook_url (str): URL for the webhook server
            secret (str, optional): Secret for webhook signature verification
        """
        self.token = token
        self.webhook_url = webhook_url
        self.secret = secret
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def create_webhook(self, repo_full_name: str) -> bool:
        """
        Create a webhook for a repository.
        
        Args:
            repo_full_name (str): Full repository name (owner/repo)
            
        Returns:
            bool: True if webhook was created successfully, False otherwise
        """
        url = f"https://api.github.com/repos/{repo_full_name}/hooks"
        
        # Webhook configuration
        data = {
            "name": "web",
            "active": True,
            "events": [
                "push",
                "pull_request",
                "create",
                "repository"
            ],
            "config": {
                "url": self.webhook_url,
                "content_type": "json",
                "insecure_ssl": "0"
            }
        }
        
        # Add secret if provided
        if self.secret:
            data["config"]["secret"] = self.secret
        
        # Create webhook
        try:
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 201:
                logger.info(f"Webhook created for {repo_full_name}")
                return True
            else:
                logger.warning(f"Failed to create webhook for {repo_full_name}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error creating webhook for {repo_full_name}: {e}")
            return False
    
    def delete_webhook(self, repo_full_name: str, hook_id: int) -> bool:
        """
        Delete a webhook from a repository.
        
        Args:
            repo_full_name (str): Full repository name (owner/repo)
            hook_id (int): ID of the webhook to delete
            
        Returns:
            bool: True if webhook was deleted successfully, False otherwise
        """
        url = f"https://api.github.com/repos/{repo_full_name}/hooks/{hook_id}"
        
        try:
            response = requests.delete(url, headers=self.headers)
            
            if response.status_code == 204:
                logger.info(f"Webhook {hook_id} deleted from {repo_full_name}")
                return True
            else:
                logger.warning(f"Failed to delete webhook {hook_id} from {repo_full_name}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error deleting webhook {hook_id} from {repo_full_name}: {e}")
            return False
    
    def get_webhooks(self, repo_full_name: str) -> List[Dict[str, Any]]:
        """
        Get all webhooks for a repository.
        
        Args:
            repo_full_name (str): Full repository name (owner/repo)
            
        Returns:
            list: List of webhook data dictionaries
        """
        url = f"https://api.github.com/repos/{repo_full_name}/hooks"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get webhooks for {repo_full_name}: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting webhooks for {repo_full_name}: {e}")
            return []
    
    def find_webhook(self, repo_full_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a webhook with the configured URL in a repository.
        
        Args:
            repo_full_name (str): Full repository name (owner/repo)
            
        Returns:
            dict or None: Webhook data if found, None otherwise
        """
        webhooks = self.get_webhooks(repo_full_name)
        
        for webhook in webhooks:
            if webhook.get("config", {}).get("url") == self.webhook_url:
                return webhook
        
        return None
    
    def setup_webhook(self, repo_full_name: str) -> bool:
        """
        Set up a webhook for a repository, creating it if it doesn't exist.
        
        Args:
            repo_full_name (str): Full repository name (owner/repo)
            
        Returns:
            bool: True if webhook is set up, False otherwise
        """
        # Check if webhook already exists
        webhook = self.find_webhook(repo_full_name)
        
        if webhook:
            logger.info(f"Webhook already exists for {repo_full_name}")
            return True
        
        # Create webhook
        return self.create_webhook(repo_full_name)
    
    def setup_webhooks_for_all_repos(self) -> Dict[str, bool]:
        """
        Set up webhooks for all repositories the user has access to.
        
        Returns:
            dict: Dictionary mapping repository names to setup success status
        """
        results = {}
        
        try:
            # Get all repositories
            response = requests.get("https://api.github.com/user/repos", headers=self.headers)
            
            if response.status_code != 200:
                logger.warning(f"Failed to get repositories: {response.status_code} - {response.text}")
                return results
            
            repos = response.json()
            
            # Set up webhooks for each repository
            for repo in repos:
                repo_full_name = repo["full_name"]
                results[repo_full_name] = self.setup_webhook(repo_full_name)
            
            return results
        except Exception as e:
            logger.error(f"Error setting up webhooks for all repositories: {e}")
            return results
    
    def handle_repository_created(self, repo_full_name: str) -> bool:
        """
        Handle repository creation event by setting up a webhook.
        
        Args:
            repo_full_name (str): Full repository name (owner/repo)
            
        Returns:
            bool: True if webhook was set up successfully, False otherwise
        """
        return self.setup_webhook(repo_full_name)
