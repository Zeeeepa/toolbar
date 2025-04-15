import logging
import requests
from typing import List, Dict, Optional, Tuple
from logging import getLogger
from github import Github
from github.Repository import Repository
from github.GithubException import GithubException, UnknownObjectException, BadCredentialsException
import concurrent.futures
from queue import Queue
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)

# Default number of worker threads
DEFAULT_WORKERS = 20

class WebhookManager:
    """
    Manages GitHub webhooks for repositories.
    Ensures all repositories have webhooks configured and keeps them updated.
    """
    
    def __init__(self, github_client: Github, webhook_url: str, max_workers: int = DEFAULT_WORKERS):
        """
        Initialize the webhook manager.
        
        Args:
            github_client: GitHub client instance
            webhook_url: URL for the webhook (e.g., https://example.com/webhook)
            max_workers: Maximum number of concurrent workers for webhook processing
        """
        self.github_client = github_client
        self.webhook_url = webhook_url
        self.events = ["push", "pull_request", "create", "delete", "repository"]
        self.max_workers = max_workers
        self.executor = None  # Will be initialized when needed
    
    def get_all_repositories(self) -> List[Repository]:
        """
        Get all repositories accessible by the GitHub token.
        
        Returns:
            List of Repository objects
        """
        try:
            logger.info("Fetching all accessible repositories")
            return list(self.github_client.get_user().get_repos())
        except BadCredentialsException as e:
            logger.error(f"Authentication error: {e}")
            raise ValueError(f"GitHub authentication failed. Please check your credentials and ensure your token has 'repo' and 'admin:repo_hook' scopes. Error: {e}")
        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            raise ValueError(f"Failed to fetch repositories: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching repositories: {e}")
            raise ValueError(f"Unexpected error fetching repositories: {e}")
    
    def list_webhooks(self, repo: Repository) -> List[Dict]:
        """
        List all webhooks for a repository.
        
        Args:
            repo: GitHub Repository object
            
        Returns:
            List of webhook dictionaries
        """
        logger.info(f"Listing webhooks for {repo.full_name}")
        try:
            hooks = []
            for hook in repo.get_hooks():
                hooks.append({
                    'id': hook.id,
                    'url': hook.url,
                    'config': hook.config,
                    'events': hook.events
                })
            return hooks
        except GithubException as e:
            if e.status == 403:
                logger.warning(f"Permission denied to list webhooks for {repo.full_name}: {e}")
                return []
            logger.error(f"Failed to list webhooks for {repo.full_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing webhooks for {repo.full_name}: {e}")
            return []
    
    def find_pr_review_webhook(self, repo: Repository) -> Optional[Dict]:
        """
        Find an existing PR review webhook in the repository.
        
        Args:
            repo: GitHub Repository object
            
        Returns:
            Webhook dictionary if found, None otherwise
        """
        hooks = self.list_webhooks(repo)
        for hook in hooks:
            if 'config' in hook and 'url' in hook['config'] and hook['config']['url'] == self.webhook_url:
                return hook
        return None
    
    def create_webhook(self, repo: Repository) -> Optional[Dict]:
        """
        Create a new webhook for PR reviews in the repository.
        
        Args:
            repo: GitHub Repository object
            
        Returns:
            Created webhook dictionary if successful, None otherwise
        """
        logger.info(f"Creating webhook for {repo.full_name}")
        try:
            logger.info(f"Creating webhook for repository {repo.full_name} with URL {self.webhook_url}")
            
            # Create webhook configuration
            config = {
                'url': self.webhook_url,
                'content_type': 'json',
                'insecure_ssl': '0'
            }
            
            # Create the webhook
            hook = repo.create_hook(
                name='web',
                config=config,
                events=self.events,
                active=True
            )
            
            logger.info(f"Webhook created successfully for {repo.full_name}")
            
            return {
                'id': hook.id,
                'url': hook.url,
                'config': hook.config,
                'events': hook.events
            }
        except GithubException as e:
            if e.status == 403:
                logger.warning(f"Permission denied to create webhook for {repo.full_name}: {e}")
                return None
            elif e.status == 401:
                logger.error(f"Authentication error creating webhook for {repo.full_name}: {e}")
                raise ValueError(f"GitHub authentication failed. Please check your credentials and ensure your token has 'repo' and 'admin:repo_hook' scopes.")
            elif e.status == 422:
                logger.warning(f"Webhook already exists or invalid inputs for {repo.full_name}: {e}")
                return None
            else:
                logger.error(f"Failed to create webhook for {repo.full_name}: {e}")
                return None
        except Exception as e:
            logger.error(f"Unexpected error creating webhook for {repo.full_name}: {e}")
            return None
    
    def update_webhook_url(self, repo: Repository, hook_id: int, new_url: str) -> bool:
        """
        Update a webhook URL.
        
        Args:
            repo: GitHub Repository object
            hook_id: Webhook ID
            new_url: New webhook URL
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Updating webhook URL for {repo.full_name}")
        try:
            hook = repo.get_hook(hook_id)
            
            # Update the webhook configuration
            config = hook.config
            config['url'] = new_url
            
            # Edit the webhook
            hook.edit(
                name='web',
                config=config,
                events=self.events,
                active=True
            )
            
            logger.info(f"Webhook URL updated successfully for {repo.full_name}")
            return True
        except GithubException as e:
            if e.status == 403:
                logger.warning(f"Permission denied to update webhook for {repo.full_name}: {e}")
                return False
            elif e.status == 401:
                logger.error(f"Authentication error updating webhook for {repo.full_name}: {e}")
                return False
            elif e.status == 404:
                logger.warning(f"Webhook not found for {repo.full_name}: {e}")
                return False
            else:
                logger.error(f"Failed to update webhook for {repo.full_name}: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error updating webhook for {repo.full_name}: {e}")
            return False
    
    def ensure_webhook_exists(self, repo: Repository) -> Tuple[bool, str]:
        """
        Ensure a webhook exists for the repository.
        Creates one if it doesn't exist, updates if URL doesn't match.
        
        Args:
            repo: GitHub Repository object
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Find existing webhook
            existing_hook = self.find_pr_review_webhook(repo)
            
            if existing_hook:
                # Check if URL needs updating
                if existing_hook['config']['url'] != self.webhook_url:
                    # Update webhook URL
                    success = self.update_webhook_url(repo, existing_hook['id'], self.webhook_url)
                    if success:
                        return True, f"Webhook URL updated for {repo.full_name}"
                    else:
                        return False, f"Failed to update webhook URL for {repo.full_name}"
                else:
                    # Webhook already exists with correct URL
                    return True, f"Webhook already exists for {repo.full_name}"
            else:
                # Create new webhook
                result = self.create_webhook(repo)
                if result:
                    return True, f"Webhook created for {repo.full_name}"
                else:
                    return False, f"Failed to create webhook for {repo.full_name}"
        except ValueError as e:
            # Pass through authentication errors
            raise
        except Exception as e:
            logger.error(f"Error ensuring webhook exists for {repo.full_name}: {e}")
            return False, f"Error: {str(e)}"
    
    def setup_webhooks_for_all_repos(self) -> Dict[str, str]:
        """
        Set up webhooks for all accessible repositories using thread pool for concurrency.
        
        Returns:
            Dictionary mapping repository names to status messages
        """
        logger.info(f"Setting up webhooks for all repositories with {self.max_workers} concurrent workers")
        results = {}
        
        try:
            logger.info("Fetching all accessible repositories")
            repos = self.get_all_repositories()
            
            if not repos:
                logger.warning("No repositories found or accessible")
                return {"status": "No repositories found or accessible"}
            
            logger.info(f"Found {len(repos)} repositories")
            
            # Use a thread pool executor for concurrent processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit each repository to the executor
                future_to_repo = {
                    executor.submit(self.ensure_webhook_exists, repo): repo
                    for repo in repos
                }
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_repo):
                    repo = future_to_repo[future]
                    try:
                        success, message = future.result()
                        results[repo.full_name] = message
                    except Exception as e:
                        logger.error(f"Error setting up webhook for {repo.full_name}: {e}")
                        results[repo.full_name] = f"Error: {str(e)}"
            
            return results
        except ValueError as e:
            # Pass through authentication errors directly to show in the UI
            raise
        except Exception as e:
            logger.error(f"Error setting up webhooks: {e}")
            return {"status": f"Error: {str(e)}"}
    
    def handle_repository_created(self, repo_name: str) -> Tuple[bool, str]:
        """
        Handle repository creation event.
        Sets up webhook for the newly created repository.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            
        Returns:
            Tuple of (success, message)
        """
        logger.info(f"Handling repository creation for {repo_name}")
        try:
            repo = self.github_client.get_repo(repo_name)
            success, message = self.ensure_webhook_exists(repo)
            print(f"New repository {repo_name}: {message}")
            return success, message
        except UnknownObjectException:
            logger.warning(f"Repository {repo_name} not found")
            return False, f"Repository {repo_name} not found"
        except BadCredentialsException:
            logger.error(f"Authentication error accessing repository {repo_name}")
            return False, f"Authentication error accessing repository {repo_name}"
        except GithubException as e:
            logger.error(f"GitHub API error handling repository creation for {repo_name}: {e}")
            return False, f"GitHub API error: {str(e)}"
        except Exception as e:
            logger.error(f"Error handling repository creation for {repo_name}: {e}")
            return False, f"Error: {str(e)}"
