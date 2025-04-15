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
        
        for project in self.projects:
            if not project.pinned:
                continue
            
            try:
                repo = self.github.get_repo(project.full_name)
                
                # Check for new PRs
                if self.notify_prs:
                    self._check_pull_requests(project, repo)
                
                # Check for new branches
                if self.notify_branches:
                    self._check_branches(project, repo)
            
            except Exception as e:
                logger.error(f"Error checking updates for {project.full_name}: {e}")
    
    def _check_pull_requests(self, project, repo):
        """Check for new pull requests in a repository."""
        try:
            # Get open PRs
            pulls = repo.get_pulls(state='open', sort='created', direction='desc')
            
            # Check the first 10 PRs (most recent)
            for i, pull in enumerate(pulls):
                if i >= 10:
                    break
                
                # Skip PRs older than 24 hours
                if datetime.now() - pull.created_at > timedelta(hours=24):
                    continue
                
                # Check if we already have this PR in notifications
                pr_url = pull.html_url
                if any(n.url == pr_url for n in project.notifications):
                    continue
                
                # Create notification
                notification = GitHubNotification(
                    title=f"New PR: {pull.title}",
                    url=pr_url,
                    created_at=pull.created_at,
                    type_str="pr",
                    repo_name=project.full_name
                )
                
                # Add notification to project
                project.add_notification(notification)
                
                # Emit signals
                self.notification_received.emit(notification)
                self.project_notification_received.emit(project, notification)
                
                # Save projects
                self.save_projects()
        
        except Exception as e:
            logger.error(f"Error checking PRs for {project.full_name}: {e}")
    
    def _check_branches(self, project, repo):
        """Check for new branches in a repository."""
        try:
            # Get branches
            branches = repo.get_branches()
            
            # Get existing branch URLs
            existing_branch_urls = {n.url for n in project.notifications if n.type == "branch"}
            
            # Check branches
            for branch in branches:
                # Skip master/main branch
                if branch.name in ('master', 'main'):
                    continue
                
                # Get branch URL
                branch_url = f"{repo.html_url}/tree/{branch.name}"
                
                # Skip if we already have this branch
                if branch_url in existing_branch_urls:
                    continue
                
                # Get commit date
                commit = branch.commit
                commit_obj = repo.get_commit(commit.sha)
                commit_date = commit_obj.commit.author.date
                
                # Skip branches older than 24 hours
                if datetime.now() - commit_date > timedelta(hours=24):
                    continue
                
                # Create notification
                notification = GitHubNotification(
                    title=f"New branch: {branch.name}",
                    url=branch_url,
                    created_at=commit_date,
                    type_str="branch",
                    repo_name=project.full_name
                )
                
                # Add notification to project
                project.add_notification(notification)
                
                # Emit signals
                self.notification_received.emit(notification)
                self.project_notification_received.emit(project, notification)
                
                # Save projects
                self.save_projects()
        
        except Exception as e:
            logger.error(f"Error checking branches for {project.full_name}: {e}")
    
    def get_user_repositories(self) -> List[GitHubProject]:
        """Get repositories for the authenticated user."""
        if not self.github:
            return []
        
        try:
            repos = []
            
            # Get user's repositories
            for repo in self.github.get_user().get_repos():
                project = GitHubProject(
                    name=repo.name,
                    full_name=repo.full_name,
                    owner=repo.owner.login,
                    url=repo.html_url,
                    icon_url=repo.owner.avatar_url
                )
                
                # Check if project is already pinned
                for existing_project in self.projects:
                    if existing_project.full_name == project.full_name:
                        project.pinned = existing_project.pinned
                        break
                
                repos.append(project)
            
            return repos
        
        except Exception as e:
            logger.error(f"Error getting user repositories: {e}")
            return []
    
    def add_project(self, project):
        """Add a project to the monitor."""
        # Check if project already exists
        for existing_project in self.projects:
            if existing_project.full_name == project.full_name:
                return existing_project
        
        # Add project
        self.projects.append(project)
        self.save_projects()
        return project
    
    def remove_project(self, project):
        """Remove a project from the monitor."""
        self.projects = [p for p in self.projects if p.full_name != project.full_name]
        self.save_projects()
    
    def pin_project(self, project, pinned=True):
        """Pin or unpin a project."""
        for p in self.projects:
            if p.full_name == project.full_name:
                p.pinned = pinned
                self.save_projects()
                return
        
        # If project doesn't exist, add it
        project.pinned = pinned
        self.add_project(project)
    
    def clear_all_notifications(self):
        """Clear all notifications for all projects."""
        for project in self.projects:
            project.clear_notifications()
        self.save_projects()
    
    def get_projects_file_path(self):
        """Get the path to the projects file."""
        config_dir = os.path.expanduser("~/.toolkit")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "github_projects.json")
    
    def load_projects(self):
        """Load projects from file."""
        try:
            file_path = self.get_projects_file_path()
            if not os.path.exists(file_path):
                return
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            self.projects = []
            for project_data in data:
                project = GitHubProject.from_dict(project_data)
                self.projects.append(project)
            
            logger.info(f"Loaded {len(self.projects)} GitHub projects")
        
        except Exception as e:
            logger.error(f"Error loading GitHub projects: {e}")
    
    def save_projects(self):
        """Save projects to file."""
        try:
            file_path = self.get_projects_file_path()
            
            data = [project.to_dict() for project in self.projects]
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(self.projects)} GitHub projects")
        
        except Exception as e:
            logger.error(f"Error saving GitHub projects: {e}")
    
    def validate_credentials(self) -> Tuple[bool, str]:
        """Validate GitHub credentials."""
        if not self.token:
            return False, "No GitHub token provided"
        
        try:
            github = Github(self.token)
            user = github.get_user()
            username = user.login
            
            return True, f"Authenticated as {username}"
        
        except Exception as e:
            return False, f"Authentication failed: {e}"
