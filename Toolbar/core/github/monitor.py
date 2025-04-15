#!/usr/bin/env python3
"""
GitHub Monitor module.
This module provides tools for monitoring GitHub repositories.
"""

import os
import sys
import json
import time
import logging
import warnings
import threading
import requests
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal

from github import Github
import importlib

from Toolbar.core.github.models import GitHubProject, GitHubNotification
from Toolbar.core.github.webhook_manager import WebhookManager
from Toolbar.core.github.ngrok_manager import NgrokManager
from Toolbar.core.github.webhook_handler import WebhookHandler

logger = logging.getLogger(__name__)

class GitHubMonitor(QObject):
    """
    Monitors GitHub repositories for new PRs and branches.
    """
    
    notification_received = pyqtSignal(object)
    project_notification_received = pyqtSignal(object, object)
    
    def __init__(self, config):
        """
        Initialize the GitHub monitor.
        
        Args:
            config: Configuration object
        """
        super().__init__()
        self.config = config
        
        # Get GitHub credentials
        self.username, self.api_token = config.get_github_credentials()
        
        # Initialize GitHub client
        self.github_client = None
        try:
            self.github_client = Github(self.api_token)
            # Test the client
            user = self.github_client.get_user()
            test_username = user.login
            logger.info(f"GitHub client initialized successfully for user: {test_username}")
            if self.username and test_username != self.username:
                logger.warning(f"GitHub username mismatch: Config has {self.username}, but token belongs to {test_username}")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
            self.github_client = None
        
        # Initialize webhook components
        self.webhook_handler = None
        self.webhook_server_thread = None
        self.webhook_manager = None
        self.ngrok_manager = None
        self.webhook_url = None
        
        # Initialize projects
        self.projects = {}  # Dictionary of GitHubProject objects keyed by full_name
        self._load_projects()
        
        # Start monitoring
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_interval = int(config.get_setting("github.monitor_interval", 300))  # Default: 5 minutes
        
        # Webhook settings
        self.webhook_enabled = self.config.get_setting("github.webhook_enabled", False)
        self.webhook_port = int(self.config.get_setting("github.webhook_port", 8000))
        self.ngrok_auth_token = self.config.get_setting("github.ngrok_auth_token", "")
        
        # Start webhook server if enabled
        if self.webhook_enabled and self.api_token and self.ngrok_auth_token:
            self.setup_webhook_server(self.webhook_port, self.ngrok_auth_token)
    
    def _load_projects(self):
        """Load pinned projects from config."""
        try:
            pinned_projects_json = self.config.get_setting("github.pinned_projects", "[]")
            pinned_projects = json.loads(pinned_projects_json)
            
            for project_data in pinned_projects:
                project = GitHubProject(
                    full_name=project_data.get("full_name", ""),
                    name=project_data.get("name", ""),
                    description=project_data.get("description", ""),
                    url=project_data.get("url", ""),
                    avatar_url=project_data.get("avatar_url", ""),
                    owner=project_data.get("owner", ""),
                    pinned=project_data.get("pinned", True)
                )
                
                # Load notifications
                for notification_data in project_data.get("notifications", []):
                    notification = GitHubNotification(
                        title=notification_data.get("title", ""),
                        message=notification_data.get("message", ""),
                        url=notification_data.get("url", ""),
                        type=notification_data.get("type", ""),
                        timestamp=notification_data.get("timestamp", time.time()),
                        read=notification_data.get("read", False)
                    )
                    project.notifications.append(notification)
                
                self.projects[project.full_name] = project
        except Exception as e:
            logger.error(f"Error loading projects: {e}")
    
    def save_projects(self):
        """Save projects to config."""
        try:
            projects_data = []
            for project in self.projects.values():
                project_data = {
                    "full_name": project.full_name,
                    "name": project.name,
                    "description": project.description,
                    "url": project.url,
                    "avatar_url": project.avatar_url,
                    "owner": project.owner,
                    "pinned": project.pinned,
                    "notifications": []
                }
                
                # Save notifications
                for notification in project.notifications:
                    notification_data = {
                        "title": notification.title,
                        "message": notification.message,
                        "url": notification.url,
                        "type": notification.type,
                        "timestamp": notification.timestamp,
                        "read": notification.read
                    }
                    project_data["notifications"].append(notification_data)
                
                projects_data.append(project_data)
            
            pinned_projects_json = json.dumps(projects_data)
            self.config.set_setting("github.pinned_projects", pinned_projects_json)
            self.config.save()
        except Exception as e:
            logger.error(f"Error saving projects: {e}")
    
    def set_credentials(self, username, token):
        """
        Set GitHub credentials.
        
        Args:
            username (str): GitHub username
            token (str): GitHub API token
        """
        if not username or not token:
            logger.warning("Empty GitHub credentials provided, will not update")
            return False, "Empty credentials provided"
        
        try:
            # Test the new credentials
            try:
                # Update the GitHub client with new credentials
                test_client = None
                
                test_client = Github(token)
                test_user = test_client.get_user()
                test_username = test_user.login
                
                # Update the client if test was successful
                self.github_client = test_client
                logger.info(f"GitHub client updated successfully for user: {test_username}")
                
                # Update the credentials in config
                self.username = username
                self.api_token = token
                
                if username != test_username:
                    logger.warning(f"GitHub username mismatch: Provided {username}, but token belongs to {test_username}")
                
                # Update webhook manager if it exists
                if self.webhook_manager:
                    self.webhook_manager.github_client = self.github_client
                
                # Save credentials to config
                self.config.set_github_credentials(username, token)
                self.config.save()
                
                return True, f"GitHub credentials updated successfully for user: {test_username}"
            
            except Exception as e:
                logger.error(f"Failed to update GitHub client with new credentials: {e}")
                return False, f"Failed to authenticate with GitHub: {str(e)}"
        
        except Exception as e:
            logger.error(f"Error setting GitHub credentials: {e}")
            return False, f"Error: {str(e)}"
    
    def start_monitoring(self):
        """Start monitoring GitHub repositories."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_thread, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring GitHub repositories."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None
    
    def _monitor_thread(self):
        """Thread function for monitoring GitHub repositories."""
        first_run = True
        while self.monitoring:
            try:
                self._check_github_updates(send_notifications=not first_run)
                first_run = False
            except Exception as e:
                warnings.warn(f"Error checking GitHub updates: {e}")
            
            # Sleep for the configured interval
            for _ in range(self.monitor_interval):
                if not self.monitoring:
                    break
                time.sleep(1)
    
    def _check_github_updates(self, send_notifications=True):
        """
        Check for GitHub updates (new PRs and branches).
        
        Args:
            send_notifications (bool): Whether to send notifications for new updates
        """
        if not self.github_client:
            return
        
        try:
            # Get repositories
            response = requests.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"token {self.api_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code == 401:
                warnings.warn(f"GitHub authentication failed (401 Unauthorized). Please check your token in the settings or .env file.")
                
                print("\nℹ️ GitHub Authentication Error")
                print("Please check your GitHub credentials:")
                print("1. Click on the GitHub icon in the toolbar to update your credentials")
                print("2. Or run the configuration script: python -m Toolbar.scripts.configure_github")
                print("3. Or add your credentials to the .env file:\n   GITHUB_USERNAME=your_username\n   GITHUB_TOKEN=your_personal_access_token\n")
                
                return
            
            if response.status_code != 200:
                warnings.warn(f"GitHub API request failed with status code {response.status_code}: {response.text}")
                return
            
            repos = response.json()
            
            # Process each repository
            for repo in repos:
                repo_full_name = repo["full_name"]
                
                # Create project if it doesn't exist
                if repo_full_name not in self.projects:
                    self.projects[repo_full_name] = GitHubProject(
                        full_name=repo_full_name,
                        name=repo["name"],
                        description=repo["description"] or "",
                        url=repo["html_url"],
                        avatar_url=repo["owner"]["avatar_url"],
                        owner=repo["owner"]["login"],
                        pinned=False
                    )
                
                # Check for PRs
                pr_url = f"https://api.github.com/repos/{repo_full_name}/pulls"
                pr_response = requests.get(pr_url, headers={"Authorization": f"token {self.api_token}", "Accept": "application/vnd.github.v3+json"})
                
                if pr_response.status_code == 200:
                    prs = pr_response.json()
                    
                    for pr in prs:
                        # Check if we already have this PR
                        pr_url = pr["html_url"]
                        project = self.projects[repo_full_name]
                        
                        # Skip if we already have this PR
                        if any(n.url == pr_url for n in project.notifications):
                            continue
                        
                        # Create notification
                        notification = GitHubNotification(
                            title=f"PR #{pr['number']}: {pr['title']}",
                            message=f"PR opened by {pr['user']['login']}",
                            url=pr_url,
                            type="pr",
                            timestamp=time.time(),
                            read=False
                        )
                        
                        # Add notification to project
                        project.notifications.append(notification)
                        
                        # Send notification signal
                        if send_notifications:
                            self.notification_received.emit(notification)
                            self.project_notification_received.emit(project, notification)
                
                # Check for branches
                branch_url = f"https://api.github.com/repos/{repo_full_name}/branches"
                branch_response = requests.get(branch_url, headers={"Authorization": f"token {self.api_token}", "Accept": "application/vnd.github.v3+json"})
                
                if branch_response.status_code == 200:
                    branches = branch_response.json()
                    
                    for branch in branches:
                        # Skip main/master branches
                        if branch["name"] in ["main", "master"]:
                            continue
                        
                        # Get the latest commit for the branch
                        commit_url = f"https://api.github.com/repos/{repo_full_name}/commits/{branch['commit']['sha']}"
                        commit_response = requests.get(commit_url, headers={"Authorization": f"token {self.api_token}", "Accept": "application/vnd.github.v3+json"})
                        
                        if commit_response.status_code == 200:
                            commit = commit_response.json()
                            commit_time = commit["commit"]["author"]["date"]
                            
                            # Skip if the commit is older than 24 hours
                            # TODO: Implement proper time comparison
                            
                            # Create notification
                            notification = GitHubNotification(
                                title=f"Branch: {branch['name']}",
                                message=f"Latest commit: {commit['commit']['message']}",
                                url=f"https://github.com/{repo_full_name}/tree/{branch['name']}",
                                type="branch",
                                timestamp=time.time(),
                                read=False
                            )
                            
                            # Add notification to project if it doesn't exist
                            project = self.projects[repo_full_name]
                            branch_url = notification.url
                            
                            # Skip if we already have this branch
                            if any(n.url == branch_url for n in project.notifications):
                                continue
                            
                            # Add notification to project
                            project.notifications.append(notification)
                            
                            # Send notification signal
                            if send_notifications:
                                self.notification_received.emit(notification)
                                self.project_notification_received.emit(project, notification)
        
        except Exception as e:
            warnings.warn(f"Error checking GitHub updates: {e}")
    
    def setup_webhook_server(self, port, ngrok_auth_token):
        """
        Set up the webhook server.
        
        Args:
            port (int): Port to run the webhook server on
            ngrok_auth_token (str): ngrok authentication token
        
        Returns:
            str: Webhook URL
        """
        try:
            # Stop existing webhook server if running
            self.stop_webhook_server()
            
            # Create webhook handler
            self.webhook_handler = WebhookHandler(self)
            
            # Start webhook server
            self.webhook_server_thread = threading.Thread(
                target=self.webhook_handler.run_server,
                args=(port,),
                daemon=True
            )
            self.webhook_server_thread.start()
            
            # Set up ngrok
            self.ngrok_manager = NgrokManager(ngrok_auth_token)
            self.webhook_url = self.ngrok_manager.start_tunnel(port)
            
            if not self.webhook_url:
                logger.error("Failed to start ngrok tunnel")
                self.stop_webhook_server()
                return None
            
            # Create webhook manager
            if self.github_client:
                self.webhook_manager = WebhookManager(self.github_client, self.webhook_url)
            
            # Update config
            self.webhook_enabled = True
            self.webhook_port = port
            self.config.set_setting("github.webhook_enabled", True)
            self.config.set_setting("github.webhook_port", port)
            
            self.ngrok_auth_token = ngrok_auth_token
            self.config.set_setting("github.ngrok_auth_token", ngrok_auth_token)
            self.config.save()
            
            logger.info(f"Webhook server started on {self.webhook_url}")
            return self.webhook_url
        
        except Exception as e:
            logger.error(f"Error setting up webhook server: {e}")
            self.stop_webhook_server()
            return None
    
    def stop_webhook_server(self):
        """
        Stop the webhook server.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Stop ngrok
            if self.ngrok_manager:
                self.ngrok_manager.stop_tunnel()
                self.ngrok_manager = None
            
            # Stop webhook server
            if self.webhook_handler:
                self.webhook_handler.stop_server()
                self.webhook_handler = None
            
            # Stop webhook server thread
            if self.webhook_server_thread:
                self.webhook_server_thread.join(timeout=1.0)
                self.webhook_server_thread = None
            
            # Update config
            self.webhook_enabled = False
            self.webhook_url = None
            self.config.set_setting("github.webhook_enabled", False)
            self.config.save()
            
            logger.info("Webhook server stopped")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping webhook server: {e}")
            return False
    
    def get_projects(self):
        """Get all projects."""
        return self.projects.values()
    
    def get_project(self, full_name):
        """Get a project by full name."""
        return self.projects.get(full_name)
    
    def add_project(self, full_name, pinned=True):
        """
        Add a project.
        
        Args:
            full_name (str): Full name of the repository (owner/repo)
            pinned (bool): Whether the project is pinned
        
        Returns:
            GitHubProject: The added project
        """
        try:
            # Check if project already exists
            if full_name in self.projects:
                project = self.projects[full_name]
                project.pinned = pinned
                self.save_projects()
                return project
            
            # Get repository information
            response = requests.get(
                f"https://api.github.com/repos/{full_name}",
                headers={
                    "Authorization": f"token {self.api_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get repository information: {response.text}")
                return None
            
            repo = response.json()
            
            # Create project
            project = GitHubProject(
                full_name=repo["full_name"],
                name=repo["name"],
                description=repo["description"] or "",
                url=repo["html_url"],
                avatar_url=repo["owner"]["avatar_url"],
                owner=repo["owner"]["login"],
                pinned=pinned
            )
            
            # Add project
            self.projects[full_name] = project
            self.save_projects()
            
            return project
        
        except Exception as e:
            logger.error(f"Error adding project: {e}")
            return None
    
    def remove_project(self, full_name):
        """
        Remove a project.
        
        Args:
            full_name (str): Full name of the repository (owner/repo)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if full_name in self.projects:
                del self.projects[full_name]
                self.save_projects()
                return True
            return False
        
        except Exception as e:
            logger.error(f"Error removing project: {e}")
            return False
    
    def handle_push_event(self, repo_full_name, ref, sender, commits):
        """
        Handle a push event from GitHub webhook.
        
        Args:
            repo_full_name (str): Full name of the repository (owner/repo)
            ref (str): Git reference (e.g., refs/heads/main)
            sender (dict): Sender information
            commits (list): List of commits
        """
        try:
            # Extract branch name from ref
            branch_name = ref.replace("refs/heads/", "")
            
            # Skip main/master branches
            if branch_name in ["main", "master"]:
                return
            
            # Create project if it doesn't exist
            if repo_full_name not in self.projects:
                response = requests.get(
                    f"https://api.github.com/repos/{repo_full_name}",
                    headers={
                        "Authorization": f"token {self.api_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get repository information: {response.text}")
                    return
                
                repo = response.json()
                
                self.projects[repo_full_name] = GitHubProject(
                    full_name=repo["full_name"],
                    name=repo["name"],
                    description=repo["description"] or "",
                    url=repo["html_url"],
                    avatar_url=repo["owner"]["avatar_url"],
                    owner=repo["owner"]["login"],
                    pinned=False
                )
            
            # Create notification
            commit_messages = "\n".join([f"- {commit['message']}" for commit in commits[:3]])
            if len(commits) > 3:
                commit_messages += f"\n- ... and {len(commits) - 3} more"
            
            notification = GitHubNotification(
                title=f"Push to {branch_name}",
                message=f"Pushed by {sender['login']}\n{commit_messages}",
                url=f"https://github.com/{repo_full_name}/commits/{branch_name}",
                type="push",
                timestamp=time.time(),
                read=False
            )
            
            # Add notification to project
            project = self.projects[repo_full_name]
            project.notifications.append(notification)
            
            # Send notification signal
            self.notification_received.emit(notification)
            self.project_notification_received.emit(project, notification)
            
            # Save projects
            self.save_projects()
        
        except Exception as e:
            logger.error(f"Error handling push event: {e}")
    
    def handle_branch_event(self, repo_full_name, ref, ref_type, sender):
        """
        Handle a branch creation event from GitHub webhook.
        
        Args:
            repo_full_name (str): Full name of the repository (owner/repo)
            ref (str): Branch name
            ref_type (str): Reference type (branch, tag)
            sender (dict): Sender information
        """
        try:
            # Skip main/master branches
            if ref in ["main", "master"]:
                return
            
            # Create project if it doesn't exist
            if repo_full_name not in self.projects:
                response = requests.get(
                    f"https://api.github.com/repos/{repo_full_name}",
                    headers={
                        "Authorization": f"token {self.api_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get repository information: {response.text}")
                    return
                
                repo = response.json()
                
                self.projects[repo_full_name] = GitHubProject(
                    full_name=repo["full_name"],
                    name=repo["name"],
                    description=repo["description"] or "",
                    url=repo["html_url"],
                    avatar_url=repo["owner"]["avatar_url"],
                    owner=repo["owner"]["login"],
                    pinned=False
                )
            
            # Create notification
            notification = GitHubNotification(
                title=f"New {ref_type}: {ref}",
                message=f"Created by {sender['login']}",
                url=f"https://github.com/{repo_full_name}/tree/{ref}",
                type=ref_type,
                timestamp=time.time(),
                read=False
            )
            
            # Add notification to project
            project = self.projects[repo_full_name]
            project.notifications.append(notification)
            
            # Send notification signal
            self.notification_received.emit(notification)
            self.project_notification_received.emit(project, notification)
            
            # Save projects
            self.save_projects()
        
        except Exception as e:
            logger.error(f"Error handling branch event: {e}")
    
    def handle_release_event(self, repo_full_name, release, sender):
        """
        Handle a release event from GitHub webhook.
        
        Args:
            repo_full_name (str): Full name of the repository (owner/repo)
            release (dict): Release information
            sender (dict): Sender information
        """
        try:
            # Create project if it doesn't exist
            if repo_full_name not in self.projects:
                response = requests.get(
                    f"https://api.github.com/repos/{repo_full_name}",
                    headers={
                        "Authorization": f"token {self.api_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get repository information: {response.text}")
                    return
                
                repo = response.json()
                
                self.projects[repo_full_name] = GitHubProject(
                    full_name=repo["full_name"],
                    name=repo["name"],
                    description=repo["description"] or "",
                    url=repo["html_url"],
                    avatar_url=repo["owner"]["avatar_url"],
                    owner=repo["owner"]["login"],
                    pinned=False
                )
            
            # Create notification
            ref = release["tag_name"]
            notification = GitHubNotification(
                title=f"New release: {ref}",
                message=f"Released by {sender['login']}\n{release['name']}",
                url=f"https://github.com/{repo_full_name}/releases/tag/{ref}",
                type="release",
                timestamp=time.time(),
                read=False
            )
            
            # Add notification to project
            project = self.projects[repo_full_name]
            project.notifications.append(notification)
            
            # Send notification signal
            self.notification_received.emit(notification)
            self.project_notification_received.emit(project, notification)
            
            # Save projects
            self.save_projects()
        
        except Exception as e:
            logger.error(f"Error handling release event: {e}")
    
    def handle_pull_request_event(self, repo_full_name, pull_request, action, sender):
        """
        Handle a pull request event from GitHub webhook.
        
        Args:
            repo_full_name (str): Full name of the repository (owner/repo)
            pull_request (dict): Pull request information
            action (str): Action (opened, closed, etc.)
            sender (dict): Sender information
        """
        try:
            # Skip if not opened or reopened
            if action not in ["opened", "reopened"]:
                return
            
            # Create project if it doesn't exist
            if repo_full_name not in self.projects:
                response = requests.get(
                    f"https://api.github.com/repos/{repo_full_name}",
                    headers={
                        "Authorization": f"token {self.api_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get repository information: {response.text}")
                    return
                
                repo = response.json()
                
                self.projects[repo_full_name] = GitHubProject(
                    full_name=repo["full_name"],
                    name=repo["name"],
                    description=repo["description"] or "",
                    url=repo["html_url"],
                    avatar_url=repo["owner"]["avatar_url"],
                    owner=repo["owner"]["login"],
                    pinned=False
                )
            
            # Create notification
            notification = GitHubNotification(
                title=f"PR #{pull_request['number']}: {pull_request['title']}",
                message=f"PR {action} by {sender['login']}",
                url=pull_request["html_url"],
                type="pr",
                timestamp=time.time(),
                read=False
            )
            
            # Add notification to project
            project = self.projects[repo_full_name]
            
            # Skip if we already have this PR
            if any(n.url == notification.url for n in project.notifications):
                return
            
            project.notifications.append(notification)
            
            # Send notification signal
            self.notification_received.emit(notification)
            self.project_notification_received.emit(project, notification)
            
            # Save projects
            self.save_projects()
        
        except Exception as e:
            logger.error(f"Error handling pull request event: {e}")
    
    def cleanup(self):
        """Clean up resources used by the GitHub monitor."""
        self.stop_monitoring()
        self.stop_webhook_server()
        self.save_projects()
