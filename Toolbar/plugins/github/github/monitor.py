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

# Import from core module structure
from Toolbar.plugins.github.github.webhook_manager import WebhookManager
from Toolbar.plugins.github.github.ngrok_manager import NgrokManager
from Toolbar.plugins.github.github.webhook_handler import WebhookHandler
from Toolbar.plugins.github.github.models import GitHubProject, GitHubNotification

# Import PR handler
from Toolbar.plugins.github.github.pr_handler import PRHandler

# Configure logging
logger = logging.getLogger(__name__)

# Suppress PyQt5 deprecation warnings
warnings.filterwarnings("ignore", message=".*sipPyTypeDict.*")

class GitHubMonitor(QObject):
    """
    Monitors GitHub repositories for new PRs and branches.
    """
    notification_received = pyqtSignal(object)
    project_notification_received = pyqtSignal(object, object)  # project, notification
    webhook_notification_received = pyqtSignal(object)  # notification
    
    def __init__(self, config, parent=None):
        """
        Initialize the GitHub monitor.
        
        Args:
            config: Configuration object
            parent: Parent QObject
        """
        super().__init__(parent)
        self.config = config
        self.username, self.api_token = config.get_github_credentials()
        
        # Initialize GitHub client
        self.github_client = None
        if self.username and self.api_token:
            try:
                self.github_client = Github(self.api_token)
                # Test the connection
                user = self.github_client.get_user()
                test_username = user.login
                logger.info(f"GitHub client initialized successfully for user: {test_username}")
                if test_username != self.username:
                    logger.warning(f"GitHub username mismatch: Config has {self.username}, but token belongs to {test_username}")
            except Exception as e:
                logger.error(f"Failed to initialize GitHub client: {e}")
                self.github_client = None
        
        # Initialize other attributes
        self.webhook_handler = None
        self.webhook_manager = None
        self.webhook_url = None
        self.ngrok_manager = None
        
        # Initialize PR handler
        self.pr_handler = PRHandler(self)
        
        self.monitoring_thread = None
        self.stop_monitoring_flag = threading.Event()
        self.last_check_time = datetime.now() - timedelta(minutes=60)  # Start with older time to check immediately
        
        self.projects = {}  # Dictionary of GitHubProject objects keyed by full_name
        self.known_prs = set()
        self.known_branches = set()
        
        # Load pinned projects
        self.load_pinned_projects()
        
        # Load webhook configuration
        self.webhook_enabled = self.config.get('github', 'webhook_enabled', False)
        self.webhook_port = int(self.config.get('github', 'webhook_port', 8000))
        self.ngrok_auth_token = self.config.get('github', 'ngrok_auth_token', '')
        
        # Start webhook server if enabled
        if self.webhook_enabled:
            self.setup_webhook_server(self.webhook_port, self.ngrok_auth_token)
    
    def get_setting(self, key, default=None):
        """
        Get a setting from the configuration.
        
        Args:
            key: Setting key
            default: Default value if setting is not found
            
        Returns:
            Setting value or default
        """
        try:
            return self.config.get('github', key, default)
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return default
            
    def set_setting(self, key, value):
        """
        Set a setting in the configuration.
        
        Args:
            key: Setting key
            value: Setting value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.config.set('github', key, value)
            return True
        except Exception as e:
            logger.error(f"Error setting {key} to {value}: {e}")
            return False

    def load_pinned_projects(self):
        """Load pinned projects from configuration."""
        try:
            pinned_projects_json = self.config.get('github', 'pinned_projects', '[]')
            pinned_projects = json.loads(pinned_projects_json)
            
            for project_data in pinned_projects:
                project = GitHubProject(
                    name=project_data.get('name', ''),
                    full_name=project_data.get('full_name', ''),
                    owner=project_data.get('owner', ''),
                    url=project_data.get('url', ''),
                    icon_url=project_data.get('icon_url', None)
                )
                project.pinned = True
                self.projects[project.full_name] = project
        except Exception as e:
            warnings.warn(f"Failed to load pinned projects: {e}")
    
    def save_projects(self):
        """Save pinned projects to configuration."""
        try:
            pinned_projects = []
            for project in self.projects.values():
                if project.pinned:
                    pinned_projects.append({
                        'name': project.name,
                        'full_name': project.full_name,
                        'owner': project.owner,
                        'url': project.url,
                        'icon_url': project.icon_url
                    })
            
            pinned_projects_json = json.dumps(pinned_projects)
            self.config.set('github', 'pinned_projects', pinned_projects_json)
        except Exception as e:
            warnings.warn(f"Failed to save pinned projects: {e}")
    
    def set_credentials(self, username, token):
        """
        Set GitHub credentials.
        
        Args:
            username (str): GitHub username
            token (str): GitHub API token
        """
        if not username or not token:
            logger.warning("Empty GitHub credentials provided, will not update")
            return
            
        self.username = username
        self.api_token = token
        
        # Update the GitHub client with new credentials
        try:
            # Test the credentials
            test_client = Github(token)
            user = test_client.get_user()
            test_username = user.login
            
            # If test successful, update the client
            self.github_client = test_client
            logger.info(f"GitHub client updated successfully for user: {test_username}")
            
            # Warning if username doesn't match
            if test_username != username:
                logger.warning(f"GitHub username mismatch: Provided {username}, but token belongs to {test_username}")
                
            # Stop and restart monitoring with new credentials
            was_monitoring = False
            if self.monitoring_thread is not None and not self.stop_monitoring_flag.is_set():
                was_monitoring = True
                self.stop_monitoring()
                
            # Restart monitoring if it was running
            if was_monitoring:
                self.start_monitoring()
                
            return True
        except Exception as e:
            logger.error(f"Failed to update GitHub client with new credentials: {e}")
            return False
    
    def start_monitoring(self):
        """Start the monitoring thread."""
        if self.monitoring_thread is not None and self.stop_monitoring_flag.is_set():
            return
            
        self.stop_monitoring_flag.clear()
        self.monitoring_thread = threading.Thread(target=self._monitor_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.stop_monitoring_flag.set()
        if self.monitoring_thread is not None:
            self.monitoring_thread.join(timeout=1.0)
            self.monitoring_thread = None
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate thread."""
        first_run = True
        
        while not self.stop_monitoring_flag.is_set():
            if self.username and self.api_token:
                try:
                    # First run just collects the current state without sending notifications
                    self._check_github_updates(send_notifications=not first_run)
                    first_run = False
                except Exception as e:
                    warnings.warn(f"Error checking GitHub updates: {e}")
            
            # Sleep for 5 minutes, checking periodically if we should stop
            for _ in range(300):
                if self.stop_monitoring_flag.is_set():
                    break
                time.sleep(1)
    
    def _check_github_updates(self, send_notifications=True):
        """
        Check for GitHub updates (new PRs and branches).
        
        Args:
            send_notifications (bool): Whether to emit notification signals
        """
        if not self.github_client:
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
                if response.status_code == 401:
                    warnings.warn(f"GitHub authentication failed (401 Unauthorized). Please check your token in the settings or .env file.")
                    # Show a more helpful warning to guide the user
                    print("\nℹ️ GitHub Authentication Error")
                    print("Please check your GitHub credentials:")
                    print("1. Click on the GitHub icon in the toolbar to update your credentials")
                    print("2. Or run the configuration script: python -m Toolbar.scripts.configure_github")
                    print("3. Or add your credentials to the .env file:\n   GITHUB_USERNAME=your_username\n   GITHUB_TOKEN=your_personal_access_token\n")
                else:
                    warnings.warn(f"Failed to get repositories: {response.status_code}")
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
                pr_response = requests.get(pr_url, headers={"Authorization": f"token {self.api_token}", "Accept": "application/vnd.github.v3+json"})
                if pr_response.status_code == 200:
                    prs = pr_response.json()
                    for pr in prs:
                        pr_id = f"{repo_full_name}#{pr['number']}"
                        
                        # Check if this is a new PR
                        if pr_id not in self.known_prs:
                            self.known_prs.add(pr_id)
                            
                            # Only send notification if not first run
                            if send_notifications:
                                created_at = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                                
                                # Only notify for PRs created after our last check
                                if created_at > self.last_check_time:
                                    notification = GitHubNotification(
                                        f"New PR in {repo_name}: {pr['title']}",
                                        pr["html_url"],
                                        created_at,
                                        "pr",
                                        repo_name,
                                        pr
                                    )
                                    
                                    # Emit signals
                                    self.notification_received.emit(notification)
                                    self.project_notification_received.emit(self.projects[repo_full_name], notification)
                                    self.projects[repo_full_name].add_notification(notification)
                
                # Check for branches
                branch_url = f"https://api.github.com/repos/{repo_full_name}/branches"
                branch_response = requests.get(branch_url, headers={"Authorization": f"token {self.api_token}", "Accept": "application/vnd.github.v3+json"})
                if branch_response.status_code == 200:
                    branches = branch_response.json()
                    for branch in branches:
                        branch_id = f"{repo_full_name}/{branch['name']}"
                        
                        # Check if this is a new branch
                        if branch_id not in self.known_branches:
                            self.known_branches.add(branch_id)
                            
                            # Only send notification if not first run
                            if send_notifications:
                                # Get the most recent commit to determine when the branch was created
                                commit_url = f"https://api.github.com/repos/{repo_full_name}/commits/{branch['commit']['sha']}"
                                commit_response = requests.get(commit_url, headers={"Authorization": f"token {self.api_token}", "Accept": "application/vnd.github.v3+json"})
                                
                                if commit_response.status_code == 200:
                                    commit = commit_response.json()
                                    created_at = datetime.strptime(commit["commit"]["committer"]["date"], "%Y-%m-%dT%H:%M:%SZ")
                                    
                                    # Only notify for branches created after our last check
                                    if created_at > self.last_check_time:
                                        notification = GitHubNotification(
                                            f"New branch in {repo_name}: {branch['name']}",
                                            f"https://github.com/{repo_full_name}/tree/{branch['name']}",
                                            created_at,
                                            "branch",
                                            repo_name,
                                            branch
                                        )
                                        
                                        # Emit signals
                                        self.notification_received.emit(notification)
                                        self.project_notification_received.emit(self.projects[repo_full_name], notification)
                                        self.projects[repo_full_name].add_notification(notification)
            
            # Update last check time
            self.last_check_time = datetime.now()
        except Exception as e:
            warnings.warn(f"Error checking GitHub updates: {e}")
    
    def setup_webhook_server(self, port=8000, ngrok_auth_token=None):
        """
        Set up webhook server.
        
        Args:
            port (int): Port to run the webhook server on
            ngrok_auth_token (str, optional): Ngrok authentication token
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initialize webhook handler
            self.webhook_handler = WebhookHandler(port)
            
            # Set up event handlers
            self.webhook_handler.on_pull_request = self._handle_pull_request_event
            self.webhook_handler.on_push = self._handle_push_event
            self.webhook_handler.on_create = self._handle_create_event
            self.webhook_handler.on_repository = self._handle_repository_event
            
            # Start webhook server
            if not self.webhook_handler.start_server():
                warnings.warn("Failed to start webhook server")
                return False
            
            # Set up ngrok tunnel if auth token provided
            if ngrok_auth_token:
                self.ngrok_manager = NgrokManager(ngrok_auth_token)
                self.webhook_url = self.ngrok_manager.start_tunnel(port)
                
                if not self.webhook_url:
                    warnings.warn("Failed to start ngrok tunnel")
                    self.webhook_handler.stop_server()
                    return False
            else:
                self.webhook_url = f"http://localhost:{port}/webhook"
            
            # Initialize webhook manager
            self.webhook_manager = WebhookManager(self.api_token, self.webhook_url)
            
            # Save webhook configuration
            self.config.set('github', 'webhook_enabled', True)
            self.config.set('github', 'webhook_port', port)
            if ngrok_auth_token:
                self.config.set('github', 'ngrok_auth_token', ngrok_auth_token)
            
            return True
        except Exception as e:
            warnings.warn(f"Failed to set up webhook server: {e}")
            return False
    
    def setup_webhooks(self):
        """
        Set up webhooks for all repositories.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.webhook_manager or not self.webhook_url:
            warnings.warn("Webhook manager or URL not initialized")
            return False
        
        success = True
        
        # Set up webhooks for all repositories
        for repo_full_name in self.projects:
            if not self.webhook_manager.setup_webhook(repo_full_name):
                warnings.warn(f"Failed to set up webhook for {repo_full_name}")
                success = False
        
        return success
    
    def stop_webhook_server(self):
        """
        Stop webhook server.
        
        Returns:
            bool: True if successful, False otherwise
        """
        success = True
        
        # Stop webhook handler
        if self.webhook_handler:
            if not self.webhook_handler.stop_server():
                success = False
        
        # Stop ngrok tunnel
        if self.ngrok_manager:
            if not self.ngrok_manager.stop_tunnel():
                success = False
        
        # Save webhook configuration
        self.config.set('github', 'webhook_enabled', False)
        
        return success
    
    def _handle_pull_request_event(self, payload: Dict[str, Any]):
        """
        Handle pull request webhook event.
        
        Args:
            payload: Event payload
        """
        try:
            action = payload.get('action')
            pr = payload.get('pull_request', {})
            repo = payload.get('repository', {})
            
            # Skip if missing essential data
            if not action or not pr or not repo:
                return
            
            # Get repo details
            repo_name = repo.get('name', '')
            repo_full_name = repo.get('full_name', '')
            
            # Ensure project exists
            if repo_full_name not in self.projects:
                self.projects[repo_full_name] = GitHubProject(
                    name=repo_name,
                    full_name=repo_full_name,
                    owner=repo.get('owner', {}).get('login', ''),
                    url=repo.get('html_url', ''),
                    icon_url=repo.get('owner', {}).get('avatar_url')
                )
            
            # Create notification for opened, reopened, or synchronized PR
            if action in ('opened', 'reopened', 'synchronize'):
                pr_id = f"{repo_full_name}#{pr.get('number')}"
                created_at = datetime.strptime(pr.get('created_at', ''), "%Y-%m-%dT%H:%M:%SZ")
                
                notification = GitHubNotification(
                    f"PR {action} in {repo_name}: {pr.get('title', '')}",
                    pr.get('html_url', ''),
                    created_at,
                    "pr",
                    repo_name,
                    payload
                )
                
                # Emit signals
                self.webhook_notification_received.emit(notification)
                self.notification_received.emit(notification)
                self.project_notification_received.emit(self.projects[repo_full_name], notification)
                self.projects[repo_full_name].add_notification(notification)
                
                # Add to known PRs
                self.known_prs.add(pr_id)
                
                # Check if PR should be auto-merged
                if self.get_setting("auto_merge_md_prompt", False):
                    self.pr_handler.handle_pull_request_event(payload)
        except Exception as e:
            warnings.warn(f"Error handling pull request event: {e}")
    
    def _handle_push_event(self, payload: Dict[str, Any]):
        """
        Handle push webhook event.
        
        Args:
            payload: Event payload
        """
        try:
            repo = payload.get('repository', {})
            
            # Skip if missing essential data
            if not repo:
                return
            
            # Get repo details
            repo_name = repo.get('name', '')
            repo_full_name = repo.get('full_name', '')
            
            # Ensure project exists
            if repo_full_name not in self.projects:
                self.projects[repo_full_name] = GitHubProject(
                    name=repo_name,
                    full_name=repo_full_name,
                    owner=repo.get('owner', {}).get('login', ''),
                    url=repo.get('html_url', ''),
                    icon_url=repo.get('owner', {}).get('avatar_url')
                )
            
            # Extract push details
            ref = payload.get('ref', '')
            branch_name = ref.replace('refs/heads/', '')
            pusher = payload.get('pusher', {}).get('name', 'Unknown')
            
            # Create notification for push
            commits = payload.get('commits', [])
            commit_count = len(commits)
            
            if commit_count > 0:
                created_at = datetime.now()
                
                # Use the most recent commit timestamp if available
                if commits and 'timestamp' in commits[0]:
                    created_at = datetime.strptime(commits[0]['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
                
                notification = GitHubNotification(
                    f"Push to {repo_name}/{branch_name}: {commit_count} commit(s) by {pusher}",
                    f"https://github.com/{repo_full_name}/commits/{branch_name}",
                    created_at,
                    "push",
                    repo_name,
                    payload
                )
                
                # Emit signals
                self.webhook_notification_received.emit(notification)
                self.notification_received.emit(notification)
                self.project_notification_received.emit(self.projects[repo_full_name], notification)
                self.projects[repo_full_name].add_notification(notification)
        except Exception as e:
            warnings.warn(f"Error handling push event: {e}")
    
    def _handle_create_event(self, payload: Dict[str, Any]):
        """
        Handle create webhook event (branch or tag creation).
        
        Args:
            payload: Event payload
        """
        try:
            ref_type = payload.get('ref_type')
            ref = payload.get('ref')
            repo = payload.get('repository', {})
            
            # Skip if missing essential data
            if not ref_type or not ref or not repo:
                return
            
            # Get repo details
            repo_name = repo.get('name', '')
            repo_full_name = repo.get('full_name', '')
            
            # Ensure project exists
            if repo_full_name not in self.projects:
                self.projects[repo_full_name] = GitHubProject(
                    name=repo_name,
                    full_name=repo_full_name,
                    owner=repo.get('owner', {}).get('login', ''),
                    url=repo.get('html_url', ''),
                    icon_url=repo.get('owner', {}).get('avatar_url')
                )
            
            # Handle branch creation
            if ref_type == 'branch':
                branch_id = f"{repo_full_name}/{ref}"
                created_at = datetime.now()
                
                notification = GitHubNotification(
                    f"New branch in {repo_name}: {ref}",
                    f"https://github.com/{repo_full_name}/tree/{ref}",
                    created_at,
                    "branch",
                    repo_name,
                    payload
                )
                
                # Emit signals
                self.webhook_notification_received.emit(notification)
                self.notification_received.emit(notification)
                self.project_notification_received.emit(self.projects[repo_full_name], notification)
                self.projects[repo_full_name].add_notification(notification)
                
                # Add to known branches
                self.known_branches.add(branch_id)
            
            # Handle tag creation
            elif ref_type == 'tag':
                created_at = datetime.now()
                
                notification = GitHubNotification(
                    f"New tag in {repo_name}: {ref}",
                    f"https://github.com/{repo_full_name}/releases/tag/{ref}",
                    created_at,
                    "tag",
                    repo_name,
                    payload
                )
                
                # Emit signals
                self.webhook_notification_received.emit(notification)
                self.notification_received.emit(notification)
                self.project_notification_received.emit(self.projects[repo_full_name], notification)
                self.projects[repo_full_name].add_notification(notification)
        except Exception as e:
            warnings.warn(f"Error handling create event: {e}")
    
    def _handle_repository_event(self, payload: Dict[str, Any]):
        """
        Handle repository webhook event.
        
        Args:
            payload: Event payload
        """
        try:
            action = payload.get('action')
            repo = payload.get('repository', {})
            
            # Skip if missing essential data
            if not action or not repo:
                return
            
            # Handle repo creation
            if action == 'created':
                repo_name = repo.get('name', '')
                repo_full_name = repo.get('full_name', '')
                
                # Create project entry
                self.projects[repo_full_name] = GitHubProject(
                    name=repo_name,
                    full_name=repo_full_name,
                    owner=repo.get('owner', {}).get('login', ''),
                    url=repo.get('html_url', ''),
                    icon_url=repo.get('owner', {}).get('avatar_url')
                )
                
                created_at = datetime.now()
                
                notification = GitHubNotification(
                    f"New repository created: {repo_name}",
                    repo.get('html_url', ''),
                    created_at,
                    "repository",
                    repo_name,
                    payload
                )
                
                # Emit signals
                self.webhook_notification_received.emit(notification)
                self.notification_received.emit(notification)
                
                # Set up webhook for the new repository
                if self.webhook_manager:
                    self.webhook_manager.handle_repository_created(repo_full_name)
        except Exception as e:
            warnings.warn(f"Error handling repository event: {e}")
