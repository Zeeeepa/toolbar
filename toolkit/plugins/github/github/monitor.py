"""
GitHub Monitor module.
This module provides tools for monitoring GitHub repositories.
"""

import os
import json
import threading
import time
import warnings
import logging
from datetime import datetime, timedelta
import requests
from PyQt5.QtCore import QObject, pyqtSignal
from github import Github
from typing import List, Dict, Optional, Any, Tuple

# Import local models
from toolkit.plugins.github.github.models import GitHubProject, GitHubNotification

# Configure logging
logger = logging.getLogger(__name__)

class GitHubMonitor(QObject):
    """
    Monitors GitHub repositories for new PRs and branches.
    """
    notification_received = pyqtSignal(object)
    project_notification_received = pyqtSignal(object, object)  # project, notification
    
    def __init__(self, config, parent=None):
        """
        Initialize the GitHub monitor.
        
        Args:
            config: Configuration object
            parent: Parent QObject
        """
        super().__init__(parent)
        self.config = config
        self.token = config.get('github', 'token', '')
        self.username = ''
        
        # Initialize GitHub client
        self.github = None
        if self.token:
            self.github = Github(self.token)
            try:
                self.username = self.github.get_user().login
            except Exception as e:
                logger.error(f"Failed to get GitHub username: {e}")
        
        # Initialize projects
        self.projects = []
        self.load_projects()
        
        # Initialize monitoring thread
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_interval = config.get('github', 'monitor_interval', 300)  # Default: 5 minutes
        
        # Initialize notification settings
        self.notify_prs = config.get('github', 'notify_prs', True)
        self.notify_branches = config.get('github', 'notify_branches', True)
    
    def validate_credentials(self) -> Tuple[bool, str]:
        """
        Validate GitHub credentials.
        
        Returns:
            Tuple[bool, str]: (is_valid, username)
        """
        if not self.token:
            return False, ""
        
        try:
            # Create a new GitHub client with the token
            github = Github(self.token)
            user = github.get_user()
            username = user.login
            return True, username
        except Exception as e:
            logger.error(f"Failed to validate GitHub credentials: {e}")
            return False, ""
    
    def start_monitoring(self):
        """Start monitoring GitHub repositories."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("GitHub monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring GitHub repositories."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None
        logger.info("GitHub monitoring stopped")
    
    def _monitor_loop(self):
        """Monitor loop that runs in a separate thread."""
        while self.monitoring:
            try:
                self.check_for_updates()
            except Exception as e:
                logger.error(f"Error in GitHub monitor loop: {e}")
            
            # Sleep for the configured interval
            for _ in range(self.monitor_interval):
                if not self.monitoring:
                    break
                time.sleep(1)
    
    def check_for_updates(self):
        """Check for updates in all projects."""
        if not self.github:
            return
        
        try:
            # Get user repositories
            user = self.github.get_user()
            repos = user.get_repos()
            
            # Check each repository for updates
            for repo in repos:
                # Skip forks if configured to do so
                if repo.fork and not self.config.get('github', 'include_forks', False):
                    continue
                
                # Get or create project
                project = self.get_project(repo.name, repo.full_name, repo.owner.login, repo.html_url)
                
                # Check for new pull requests
                if self.notify_prs:
                    self._check_pull_requests(project, repo)
                
                # Check for new branches
                if self.notify_branches:
                    self._check_branches(project, repo)
        
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
    
    def _check_pull_requests(self, project, repo):
        """
        Check for new pull requests in a repository.
        
        Args:
            project (GitHubProject): The project to check
            repo: The GitHub repository object
        """
        try:
            # Get open pull requests
            pulls = repo.get_pulls(state='open')
            
            # Check each pull request
            for pull in pulls:
                # Skip if already notified
                if any(n.url == pull.html_url for n in project.notifications):
                    continue
                
                # Create notification
                notification = GitHubNotification(
                    title=f"New PR: {pull.title}",
                    url=pull.html_url,
                    created_at=pull.created_at,
                    type_str="pr",
                    repo_name=project.full_name
                )
                
                # Add to project
                project.add_notification(notification)
                
                # Emit signals
                self.notification_received.emit(notification)
                self.project_notification_received.emit(project, notification)
                
                logger.info(f"New PR notification: {notification.title}")
        
        except Exception as e:
            logger.error(f"Error checking pull requests for {project.full_name}: {e}")
    
    def _check_branches(self, project, repo):
        """
        Check for new branches in a repository.
        
        Args:
            project (GitHubProject): The project to check
            repo: The GitHub repository object
        """
        try:
            # Get branches
            branches = repo.get_branches()
            
            # Get known branch names
            known_branches = set()
            for notification in project.notifications:
                if notification.type == "branch" and notification.payload:
                    known_branches.add(notification.payload.get("name", ""))
            
            # Check each branch
            for branch in branches:
                # Skip if already notified
                if branch.name in known_branches:
                    continue
                
                # Skip default branch
                if branch.name == repo.default_branch:
                    continue
                
                # Create notification
                notification = GitHubNotification(
                    title=f"New branch: {branch.name}",
                    url=f"{repo.html_url}/tree/{branch.name}",
                    created_at=datetime.now(),
                    type_str="branch",
                    repo_name=project.full_name,
                    payload={"name": branch.name}
                )
                
                # Add to project
                project.add_notification(notification)
                
                # Emit signals
                self.notification_received.emit(notification)
                self.project_notification_received.emit(project, notification)
                
                logger.info(f"New branch notification: {notification.title}")
                
                # Add to known branches
                known_branches.add(branch.name)
        
        except Exception as e:
            logger.error(f"Error checking branches for {project.full_name}: {e}")
    
    def get_project(self, name, full_name, owner, url):
        """
        Get or create a project.
        
        Args:
            name (str): Project name
            full_name (str): Full repository name (owner/repo)
            owner (str): Repository owner
            url (str): Repository URL
        
        Returns:
            GitHubProject: The project
        """
        # Check if project already exists
        for project in self.projects:
            if project.full_name == full_name:
                return project
        
        # Create new project
        project = GitHubProject(name, full_name, owner, url)
        self.projects.append(project)
        
        return project
    
    def get_user_repositories(self):
        """
        Get repositories for the authenticated user.
        
        Returns:
            List[GitHubProject]: List of projects
        """
        if not self.github:
            return []
        
        try:
            # Get user repositories
            user = self.github.get_user()
            repos = user.get_repos()
            
            # Convert to projects
            projects = []
            for repo in repos:
                # Skip forks if configured to do so
                if repo.fork and not self.config.get('github', 'include_forks', False):
                    continue
                
                project = self.get_project(repo.name, repo.full_name, repo.owner.login, repo.html_url)
                projects.append(project)
            
            return projects
        
        except Exception as e:
            logger.error(f"Error getting user repositories: {e}")
            return []
    
    def pin_project(self, project, pinned=True):
        """
        Pin or unpin a project.
        
        Args:
            project (GitHubProject): The project to pin/unpin
            pinned (bool, optional): Whether to pin or unpin the project
        """
        project.pinned = pinned
        self.save_projects()
    
    def load_projects(self):
        """Load projects from configuration."""
        try:
            projects_json = self.config.get('github', 'projects', '[]')
            projects_data = json.loads(projects_json)
            
            self.projects = []
            for project_data in projects_data:
                project = GitHubProject.from_dict(project_data)
                self.projects.append(project)
            
            logger.info(f"Loaded {len(self.projects)} projects from configuration")
        
        except Exception as e:
            logger.error(f"Error loading projects: {e}")
            self.projects = []
    
    def save_projects(self):
        """Save projects to configuration."""
        try:
            projects_data = [project.to_dict() for project in self.projects]
            projects_json = json.dumps(projects_data)
            
            self.config.set('github', 'projects', projects_json)
            self.config.save()
            
            logger.info(f"Saved {len(self.projects)} projects to configuration")
        
        except Exception as e:
            logger.error(f"Error saving projects: {e}")
    
    def clear_all_notifications(self):
        """Clear all notifications for all projects."""
        for project in self.projects:
            project.clear_notifications()
        
        self.save_projects()
