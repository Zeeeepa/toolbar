#!/usr/bin/env python3
"""
Events plugin for the Toolbar application.

This plugin provides a visual node-based flow editor for creating event-driven automations.
It integrates with other plugins like GitHub and Linear to trigger events and perform actions.
"""

import os
import sys
import json
import logging
import threading
import time
from typing import Dict, List, Any, Optional, Type, Callable, Set, Union, Tuple
from PyQt5.QtCore import QObject, pyqtSignal

# Import plugin system
from Toolbar.core.plugin_system import Plugin

# Import event system
from Toolbar.plugins.events.core.event_manager import EventManager
from Toolbar.plugins.events.core.event_system import EventType

# Import UI
from Toolbar.plugins.events.ui.events_ui import EventsUI

# Set up logger
logger = logging.getLogger(__name__)

class EventsPlugin(Plugin):
    """Events plugin for the Toolbar application."""
    
    def __init__(self):
        """Initialize the Events plugin."""
        super().__init__()

    def initialize(self, config, event_bus, toolbar):
        """
        Initialize the Events plugin.
        
        Args:
            config: Application configuration
            event_bus: Event bus for communication
            toolbar: Toolbar widget for integration
            
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Initialize event manager
            self.event_manager = EventManager(config)
            
            # Initialize UI
            self.events_ui = EventsUI(self.event_manager)
            
            # Register event handlers for GitHub events
            try:
                from Toolbar.main import get_plugin_instance
                
                github_plugin = get_plugin_instance("GitHub Integration")
                if github_plugin and hasattr(github_plugin, 'github_manager') and github_plugin.github_manager:
                    github_manager = github_plugin.github_manager
                    if hasattr(github_manager, 'notification_received'):
                        # Connect GitHub events to event manager
                        github_manager.notification_received.connect(self._handle_github_notification)
                        logger.info("Connected to GitHub events")
            except Exception as e:
                logger.warning(f"Could not connect to GitHub events: {e}")
            
            # Register event handlers for Linear events
            try:
                from Toolbar.main import get_plugin_instance
                
                linear_plugin = get_plugin_instance("Linear Integration")
                if linear_plugin and hasattr(linear_plugin, 'integration') and linear_plugin.integration:
                    linear_integration = linear_plugin.integration
                    
                    # Connect Linear issue created event
                    if hasattr(linear_integration, 'issue_created'):
                        linear_integration.issue_created.connect(self._handle_linear_issue_created)
                        logger.info("Connected to Linear issue created events")
                    
                    # Add custom signals for issue updated and closed if they don't exist
                    if not hasattr(linear_integration, 'issue_updated'):
                        linear_integration.issue_updated = pyqtSignal(object)
                        logger.info("Added Linear issue updated signal")
                    
                    if not hasattr(linear_integration, 'issue_closed'):
                        linear_integration.issue_closed = pyqtSignal(object)
                        logger.info("Added Linear issue closed signal")
                    
                    # Connect the signals
                    linear_integration.issue_updated.connect(self._handle_linear_issue_updated)
                    linear_integration.issue_closed.connect(self._handle_linear_issue_closed)
                    
                    logger.info("Connected to Linear events")
            except Exception as e:
                logger.warning(f"Could not connect to Linear events: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Events plugin: {e}", exc_info=True)
            return False
    
    def _handle_github_notification(self, notification):
        """
        Handle GitHub notification and trigger appropriate events.
        
        Args:
            notification: GitHub notification object
        """
        if not self.event_manager:
            return
            
        # Extract event data from notification
        event_data = notification.data
        event_type = None
        
        # Determine event type based on notification type
        if notification.type == "pull_request" and notification.action == "opened":
            event_type = "github_pr_created"
        elif notification.type == "pull_request" and notification.action in ["synchronize", "edited"]:
            event_type = "github_pr_updated"
        elif notification.type == "pull_request" and notification.action == "closed" and event_data.get("pull_request", {}).get("merged", False):
            event_type = "github_pr_merged"
        elif notification.type == "create" and notification.ref_type == "branch":
            event_type = "github_branch_created"
        elif notification.type == "push":
            event_type = "github_repo_updated"
            
        # Trigger event if type is determined
        if event_type:
            from Toolbar.plugins.events.core.event_system import EventType
            try:
                event_type_enum = EventType(event_type)
                self.event_manager.trigger_event(event_type_enum, event_data)
                logger.info(f"Triggered event: {event_type}")
            except ValueError:
                logger.warning(f"Unknown event type: {event_type}")
    
    def _handle_linear_issue_created(self, issue_data):
        """
        Handle Linear issue created event.
        
        Args:
            issue_data: Linear issue data
        """
        if not self.event_manager:
            return
            
        # Trigger event
        from Toolbar.plugins.events.core.event_system import EventType
        try:
            event_type_enum = EventType.LINEAR_ISSUE_CREATED
            self.event_manager.trigger_event(event_type_enum, issue_data)
            logger.info(f"Triggered event: linear_issue_created")
        except Exception as e:
            logger.warning(f"Error triggering Linear issue created event: {e}")
    
    def _handle_linear_issue_updated(self, issue_data):
        """
        Handle Linear issue updated event.
        
        Args:
            issue_data: Linear issue data
        """
        if not self.event_manager:
            return
            
        # Trigger event
        from Toolbar.plugins.events.core.event_system import EventType
        try:
            event_type_enum = EventType.LINEAR_ISSUE_UPDATED
            self.event_manager.trigger_event(event_type_enum, issue_data)
            logger.info(f"Triggered event: linear_issue_updated")
        except Exception as e:
            logger.warning(f"Error triggering Linear issue updated event: {e}")
    
    def _handle_linear_issue_closed(self, issue_data):
        """
        Handle Linear issue closed event.
        
        Args:
            issue_data: Linear issue data
        """
        if not self.event_manager:
            return
            
        # Trigger event
        from Toolbar.plugins.events.core.event_system import EventType
        try:
            event_type_enum = EventType.LINEAR_ISSUE_CLOSED
            self.event_manager.trigger_event(event_type_enum, issue_data)
            logger.info(f"Triggered event: linear_issue_closed")
        except Exception as e:
            logger.warning(f"Error triggering Linear issue closed event: {e}")
    
    def get_icon(self):
        """Get the icon for the plugin to display in the taskbar."""
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "events.svg")
        return icon_path
    
    def get_toolbar_widget(self):
        """Get the toolbar widget for the plugin."""
        if self.events_ui:
            return self.events_ui.events_button
        return None
    
    def handle_toolbar_action(self):
        """Handle toolbar action (button click)."""
        if self.events_ui:
            self.events_ui.show_events_dialog()
    
    def cleanup(self):
        """Clean up plugin resources."""
        if self.event_manager:
            self.event_manager.cleanup()
    
    @property
    def name(self) -> str:
        return "Events"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Create event-driven automations with a visual node-based flow editor."
