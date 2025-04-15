import os
import json
import threading
import time
import logging
import webbrowser
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Set

import requests
from PyQt5.QtCore import QObject, pyqtSignal

from .models import GitHubNotification, GitHubProject

# Configure logging
logger = logging.getLogger(__name__)

class GitHubMonitor(QObject):
    """
    Monitors GitHub repositories for new PRs and branches.
    Emits signals when new notifications are received.
    """
    # Signal emitted when a new notification is received
    notification_received = pyqtSignal(object)
    
    # Signal emitted when a project-specific notification is received (project, notification)
    project_notification_received = pyqtSignal(object, object)
    
    # Signal emitted when GitHub data is refreshed
    data_refreshed = pyqtSignal()
    
    def __init__(self, config, parent=None):
        """
        Initialize the GitHub monitor.
        
        Args:
            config: Configuration object with GitHub settings
            parent: Parent QObject
        """
        super().__init__(parent)
        self.config = config
        
        # Get GitHub credentials from config
        self.username = config.get('github', 'username', '')
        self.api_token = config.get('github', 'token', '')
        
        # Initialize collections
        self.projects: Dict[str, GitHubProject] = {}
        self.known_prs: Set[str] = set()
        self.known_branches: Set[str] = set()
        
        # Initialize monitoring thread
        self.monitoring_thread = None
        self.stop_monitoring_flag = threading.Event()
        self.last_check_time = datetime.now() - timedelta(minutes=60)  # Start with older time to check immediately
        
        # Load saved projects
        self.load_projects()
    
    def set_credentials(self, username: str, token: str) -> bool:
        """
        Set GitHub credentials.
        
        Args:
            username: GitHub username
            token: GitHub API token
            
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        if not username or not token:
            logger.warning("Empty GitHub credentials provided")
            return False
            
        # Test the credentials
        try:
            response = requests.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code == 200:
                # Credentials are valid
                self.username = username
                self.api_token = token
                
                # Save to config
                self.config.set('github', 'username', username)
                self.config.set('github', 'token', token)
                self.config.save()
                
                # Restart monitoring if it was running
                was_monitoring = False
                if self.monitoring_thread is not None and not self.stop_monitoring_flag.is_set():
                    was_monitoring = True
                    self.stop_monitoring()
                    
                if was_monitoring:
                    self.start_monitoring()
                
                return True
            else:
                logger.error(f"Invalid GitHub credentials: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error testing GitHub credentials: {e}")
            return False
    
    def start_monitoring(self):
        """Start the monitoring thread."""
        if self.monitoring_thread is not None and not self.stop_monitoring_flag.is_set():
            return
            
        self.stop_monitoring_flag.clear()
        self.monitoring_thread = threading.Thread(target=self._monitor_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        logger.info("GitHub monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.stop_monitoring_flag.set()
        if self.monitoring_thread is not None:
            self.monitoring_thread.join(timeout=1.0)
            self.monitoring_thread = None
        logger.info("GitHub monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate thread."""
        first_run = True
        
        while not self.stop_monitoring_flag.is_set():
            if self.username and self.api_token:
                try:
                    # First run just collects the current state without sending notifications
                    self.check_github_updates(send_notifications=not first_run)
                    first_run = False
                except Exception as e:
                    logger.error(f"Error checking GitHub updates: {e}")
            
            # Sleep for 5 minutes, checking periodically if we should stop
            for _ in range(300):
                if self.stop_monitoring_flag.is_set():
                    break
                time.sleep(1)
    
    def check_github_updates(self, send_notifications=True):
        """
        Check for GitHub updates (new PRs and branches).
        
        Args:
            send_notifications: Whether to emit notification signals
        """
        if not self.username or not self.api_token:
            logger.warning("GitHub credentials not set")
            return
        
        try:
            # Fetch repositories the authenticated user has access to
            response = requests.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"token {self.api_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get repositories: {response.status_code}")
                return
            
            repos = response.json()
            
            for repo in repos:
                repo_name = repo["name"]
                repo_full_name = repo["full_name"]
                
                # Create or update project
                if repo_full_name not in self.projects:
                    self.projects[repo_full_name] = GitHubProject(
                        name=repo_name,
                        full_name=repo_full_name,
                        owner=repo["owner"]["login"],
                        url=repo["html_url"],
                        icon_url=repo["owner"].get("avatar_url")
                    )
                
                # Check for PRs
                pr_url = f"https://api.github.com/repos/{repo_full_name}/pulls"
                pr_response = requests.get(
                    pr_url, 
                    headers={
                        "Authorization": f"token {self.api_token}", 
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                
                if pr_response.status_code == 200:
                    prs = pr_response.json()
                    for pr in prs:
                        pr_id = f"{repo_full_name}#{pr['number']}"
                        
                        # Check if this is a new PR
                        if pr_id not in self.known_prs:
                            self.known_prs.add(pr_id)
                            
                            # Only send notification if requested and not first run
                            if send_notifications:
                                created_at = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                                
                                # Only notify for recent PRs (created in the last 24 hours)
                                if datetime.now() - created_at < timedelta(hours=24):
                                    notification = GitHubNotification(
                                        f"New PR in {repo_name}: {pr['title']}",
                                        pr["html_url"],
                                        created_at,
                                        "pr",
                                        repo_name
                                    )
                                    
                                    # Emit signals
                                    self.notification_received.emit(notification)
                                    self.project_notification_received.emit(self.projects[repo_full_name], notification)
                                    self.projects[repo_full_name].add_notification(notification)
                
                # Check for branches
                branches_url = f"https://api.github.com/repos/{repo_full_name}/branches"
                branches_response = requests.get(
                    branches_url, 
                    headers={
                        "Authorization": f"token {self.api_token}", 
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                
                if branches_response.status_code == 200:
                    branches = branches_response.json()
                    for branch in branches:
                        branch_name = branch["name"]
                        branch_id = f"{repo_full_name}/{branch_name}"
                        
                        # Check if this is a new branch
                        if branch_id not in self.known_branches:
                            self.known_branches.add(branch_id)
                            
                            # Only send notification if requested and not first run
                            if send_notifications:
                                # Get the latest commit to determine when the branch was created
                                commit_url = f"https://api.github.com/repos/{repo_full_name}/commits/{branch_name}"
                                commit_response = requests.get(
                                    commit_url, 
                                    headers={
                                        "Authorization": f"token {self.api_token}", 
                                        "Accept": "application/vnd.github.v3+json"
                                    }
                                )
                                
                                if commit_response.status_code == 200:
                                    commit = commit_response.json()
                                    created_at = datetime.strptime(commit["commit"]["committer"]["date"], "%Y-%m-%dT%H:%M:%SZ")
                                    
                                    # Only notify for recent branches (created in the last 24 hours)
                                    if datetime.now() - created_at < timedelta(hours=24):
                                        notification = GitHubNotification(
                                            f"New branch in {repo_name}: {branch_name}",
                                            f"https://github.com/{repo_full_name}/tree/{branch_name}",
                                            created_at,
                                            "branch",
                                            repo_name
                                        )
                                        
                                        # Emit signals
                                        self.notification_received.emit(notification)
                                        self.project_notification_received.emit(self.projects[repo_full_name], notification)
                                        self.projects[repo_full_name].add_notification(notification)
            
            # Save projects after update
            self.save_projects()
            
            # Emit data refreshed signal
            self.data_refreshed.emit()
            
        except Exception as e:
            logger.error(f"Error checking GitHub updates: {e}")
    
    def get_projects(self) -> List[GitHubProject]:
        """Get all GitHub projects."""
        return list(self.projects.values())
    
    def get_pinned_projects(self) -> List[GitHubProject]:
        """Get pinned GitHub projects."""
        return [p for p in self.projects.values() if p.pinned]
    
    def pin_project(self, project_full_name: str, pin: bool = True) -> bool:
        """
        Pin or unpin a project.
        
        Args:
            project_full_name: Full name of the project (owner/repo)
            pin: Whether to pin (True) or unpin (False) the project
            
        Returns:
            bool: True if successful, False otherwise
        """
        if project_full_name in self.projects:
            self.projects[project_full_name].pinned = pin
            self.save_projects()
            return True
        return False
    
    def set_project_notification_settings(self, project_full_name: str, 
                                         show_pr_notifications: bool, 
                                         show_branch_notifications: bool) -> bool:
        """
        Set notification settings for a project.
        
        Args:
            project_full_name: Full name of the project (owner/repo)
            show_pr_notifications: Whether to show PR notifications
            show_branch_notifications: Whether to show branch notifications
            
        Returns:
            bool: True if successful, False otherwise
        """
        if project_full_name in self.projects:
            self.projects[project_full_name].show_pr_notifications = show_pr_notifications
            self.projects[project_full_name].show_branch_notifications = show_branch_notifications
            self.save_projects()
            return True
        return False
    
    def clear_project_notifications(self, project_full_name: str) -> bool:
        """
        Clear all notifications for a project.
        
        Args:
            project_full_name: Full name of the project (owner/repo)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if project_full_name in self.projects:
            self.projects[project_full_name].notifications = []
            self.save_projects()
            return True
        return False
    
    def clear_all_notifications(self) -> None:
        """Clear all notifications for all projects."""
        for project in self.projects.values():
            project.notifications = []
        self.save_projects()
    
    def open_notification(self, notification: GitHubNotification) -> None:
        """
        Open a notification URL in the default browser.
        
        Args:
            notification: The notification to open
        """
        webbrowser.open(notification.url)
        notification.read = True
        self.save_projects()
    
    def load_projects(self) -> None:
        """Load projects from configuration."""
        try:
            projects_json = self.config.get('github', 'projects', '[]')
            projects_data = json.loads(projects_json)
            
            for project_data in projects_data:
                project = GitHubProject.from_dict(project_data)
                self.projects[project.full_name] = project
                
                # Add known PRs and branches
                for notification in project.notifications:
                    if notification.type == 'pr' and notification.url:
                        # Extract PR ID from URL
                        pr_id = f"{project.full_name}#{notification.url.split('/')[-1]}"
                        self.known_prs.add(pr_id)
                    elif notification.type == 'branch' and notification.url:
                        # Extract branch name from URL
                        branch_name = notification.url.split('/')[-1]
                        branch_id = f"{project.full_name}/{branch_name}"
                        self.known_branches.add(branch_id)
                        
            logger.info(f"Loaded {len(self.projects)} projects from configuration")
        except Exception as e:
            logger.error(f"Failed to load projects: {e}")
    
    def save_projects(self) -> None:
        """Save projects to configuration."""
        try:
            projects_data = [p.to_dict() for p in self.projects.values()]
            projects_json = json.dumps(projects_data)
            self.config.set('github', 'projects', projects_json)
            self.config.save()
            logger.info(f"Saved {len(self.projects)} projects to configuration")
        except Exception as e:
            logger.error(f"Failed to save projects: {e}")
