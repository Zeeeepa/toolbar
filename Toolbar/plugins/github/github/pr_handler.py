"""
GitHub PR Handler module.
This module provides tools for handling GitHub pull requests, including auto-merge functionality.
"""

import os
import json
import logging
import warnings
from typing import List, Dict, Any, Optional
from github import Github, GithubException

# Configure logging
logger = logging.getLogger(__name__)

class PRHandler:
    """
    Handles GitHub pull requests, including auto-merge functionality.
    """
    
    def __init__(self, github_monitor):
        """
        Initialize the PR handler.
        
        Args:
            github_monitor: The GitHub monitor instance
        """
        self.github_monitor = github_monitor
        self.config = github_monitor.config
        
    def check_auto_merge_eligibility(self, repo_name: str, pr_number: int) -> bool:
        """
        Check if a PR is eligible for auto-merge based on configured rules.
        
        Args:
            repo_name: Full name of the repository (owner/repo)
            pr_number: Pull request number
            
        Returns:
            bool: True if PR is eligible for auto-merge, False otherwise
        """
        if not self.github_monitor.github_client:
            logger.warning("GitHub client not initialized, cannot check auto-merge eligibility")
            return False
            
        # Check if auto-merge for .md and .prompt files is enabled
        auto_merge_md_prompt = self.config.get_setting("github.auto_merge_md_prompt", False)
        if not auto_merge_md_prompt:
            return False
            
        try:
            # Get repository and pull request
            repo = self.github_monitor.github_client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Check if PR is open
            if pr.state != "open":
                return False
                
            # Get files changed in the PR
            files = pr.get_files()
            
            # Check if all files are .md or .prompt files
            for file in files:
                file_name = file.filename
                if not (file_name.endswith('.md') or file_name.endswith('.prompt')):
                    # Found a file that's not .md or .prompt
                    return False
                    
            # All checks passed, PR is eligible for auto-merge
            return True
            
        except Exception as e:
            logger.error(f"Error checking auto-merge eligibility for {repo_name}#{pr_number}: {e}")
            return False
    
    def auto_merge_pr(self, repo_name: str, pr_number: int) -> bool:
        """
        Auto-merge a pull request if it meets the criteria.
        
        Args:
            repo_name: Full name of the repository (owner/repo)
            pr_number: Pull request number
            
        Returns:
            bool: True if PR was merged successfully, False otherwise
        """
        if not self.github_monitor.github_client:
            logger.warning("GitHub client not initialized, cannot auto-merge PR")
            return False
            
        try:
            # Check if PR is eligible for auto-merge
            if not self.check_auto_merge_eligibility(repo_name, pr_number):
                logger.info(f"PR {repo_name}#{pr_number} is not eligible for auto-merge")
                return False
                
            # Get repository and pull request
            repo = self.github_monitor.github_client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Check if PR can be merged
            if not pr.mergeable:
                logger.warning(f"PR {repo_name}#{pr_number} cannot be merged (conflicts)")
                return False
                
            # Merge the PR
            merge_result = pr.merge(
                commit_title=f"Auto-merge PR #{pr_number}: {pr.title}",
                commit_message="Auto-merged by GitHub Toolbar plugin",
                merge_method="merge"
            )
            
            if merge_result.merged:
                logger.info(f"Successfully auto-merged PR {repo_name}#{pr_number}")
                return True
            else:
                logger.warning(f"Failed to auto-merge PR {repo_name}#{pr_number}: {merge_result.message}")
                return False
                
        except GithubException as e:
            logger.error(f"GitHub error auto-merging PR {repo_name}#{pr_number}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error auto-merging PR {repo_name}#{pr_number}: {e}")
            return False
            
    def handle_pull_request_event(self, payload: Dict[str, Any]) -> None:
        """
        Handle pull request webhook event and apply auto-merge if applicable.
        
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
                
            # Only process opened or synchronized PRs
            if action not in ('opened', 'reopened', 'synchronize'):
                return
                
            # Get repo details
            repo_full_name = repo.get('full_name', '')
            pr_number = pr.get('number')
            
            # Check if PR should be auto-merged
            if self.check_auto_merge_eligibility(repo_full_name, pr_number):
                logger.info(f"PR {repo_full_name}#{pr_number} is eligible for auto-merge, attempting to merge")
                self.auto_merge_pr(repo_full_name, pr_number)
                
        except Exception as e:
            logger.error(f"Error handling pull request event for auto-merge: {e}")
