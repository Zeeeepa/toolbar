#!/usr/bin/env python3
import os
import sys
import json
import logging
import threading
import time
from typing import Dict, List, Any, Optional, Type, Callable, Set, Union, Tuple
from PyQt5.QtCore import QObject, pyqtSignal

# Import event system
from Toolbar.plugins.events.core.event_system import (
    EventManager as BaseEventManager,
    Event, EventTrigger, Action, Condition, ActionParameter,
    EventType, ActionType
)

logger = logging.getLogger(__name__)

class EventManager(BaseEventManager):
    """Extended event manager with additional functionality."""
    
    def __init__(self, config):
        """Initialize the event manager."""
        super().__init__(config)
        
        # Register additional action handlers
        self.register_additional_action_handlers()
    
    def register_additional_action_handlers(self):
        """Register additional action handlers."""
        try:
            # Import handlers from other plugins
            from Toolbar.plugins.github.github.pr_handler import PRHandler
            from Toolbar.main import get_plugin_instance
            
            # Get GitHub plugin
            github_plugin = get_plugin_instance("GitHub Integration")
            if github_plugin and hasattr(github_plugin, 'github_manager') and github_plugin.github_manager:
                github_monitor = github_plugin.github_manager.github_monitor
                if github_monitor:
                    # Create PR handler
                    pr_handler = PRHandler(github_monitor)
                    
                    # Register auto-merge handler
                    self.register_action_handler(
                        ActionType.AUTO_MERGE_PR,
                        lambda action, data: self._handle_auto_merge_pr(action, data, pr_handler)
                    )
                    logger.info("Registered GitHub PR auto-merge handler")
        except Exception as e:
            logger.warning(f"Could not register GitHub PR handler: {e}")
            
        try:
            # Import Linear handlers if available
            from Toolbar.plugins.linear.linear_client import LinearClient
            from Toolbar.main import get_plugin_instance
            
            # Get Linear plugin
            linear_plugin = get_plugin_instance("Linear Integration")
            if linear_plugin and hasattr(linear_plugin, 'linear_client'):
                linear_client = linear_plugin.linear_client
                
                # Register Linear issue creation handler
                self.register_action_handler(
                    ActionType.CREATE_LINEAR_ISSUE,
                    lambda action, data: self._handle_create_linear_issue(action, data, linear_client)
                )
                logger.info("Registered Linear issue creation handler")
        except Exception as e:
            logger.warning(f"Could not register Linear handlers: {e}")
    
    def _handle_auto_merge_pr(self, action: Action, data: Dict[str, Any], pr_handler) -> Dict[str, Any]:
        """
        Handle auto-merge PR action with the PR handler.
        
        Args:
            action: The action to execute
            data: Event data
            pr_handler: PR handler instance
            
        Returns:
            Result of the action
        """
        # Get parameters
        repo = None
        pr_number = None
        
        for param in action.parameters:
            if param.name == "repo":
                repo = param.value
            elif param.name == "pr_number":
                try:
                    pr_number = int(param.value)
                except ValueError:
                    pr_number = None
        
        # If PR number not provided, try to get it from the event data
        if not pr_number and "pull_request" in data and "number" in data["pull_request"]:
            pr_number = data["pull_request"]["number"]
        
        # If repo not provided, try to get it from the event data
        if not repo and "repository" in data and "full_name" in data["repository"]:
            repo = data["repository"]["full_name"]
        
        if not repo or not pr_number:
            logger.error("Missing repo or PR number for auto-merge action")
            return {"status": "error", "message": "Missing repo or PR number"}
        
        # Auto-merge the PR
        success = pr_handler.auto_merge_pr(repo, pr_number)
        
        if success:
            return {
                "status": "success",
                "message": f"PR #{pr_number} in {repo} auto-merged successfully",
                "repo": repo,
                "pr_number": pr_number
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to auto-merge PR #{pr_number} in {repo}",
                "repo": repo,
                "pr_number": pr_number
            }
    
    def _handle_create_linear_issue(self, action: Action, data: Dict[str, Any], linear_client) -> Dict[str, Any]:
        """
        Handle create Linear issue action with the Linear client.
        
        Args:
            action: The action to execute
            data: Event data
            linear_client: Linear client instance
            
        Returns:
            Result of the action
        """
        # Get parameters
        team_id = None
        title_template = None
        description_template = None
        
        for param in action.parameters:
            if param.name == "team_id":
                team_id = param.value
            elif param.name == "title_template":
                title_template = param.value
            elif param.name == "description_template":
                description_template = param.value
        
        if not title_template:
            logger.error("Missing title_template parameter for Linear issue creation")
            return {"status": "error", "message": "Missing title template"}
        
        # Render the templates with data
        title = self._render_template(title_template, data)
        description = self._render_template(description_template, data) if description_template else ""
        
        # Create the Linear issue
        try:
            issue = linear_client.create_issue(title, description, team_id)
            
            return {
                "status": "success",
                "message": f"Linear issue created: {title}",
                "issue_id": issue.id,
                "issue_url": issue.url
            }
        except Exception as e:
            logger.error(f"Error creating Linear issue: {e}")
            return {
                "status": "error",
                "message": f"Failed to create Linear issue: {str(e)}",
                "title": title
            }
    
    def cleanup(self):
        """Clean up resources used by the event manager."""
        # Nothing to clean up for now
        pass
