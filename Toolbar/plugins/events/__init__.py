"""
Events plugin for the Toolbar application.
This plugin provides a visual node-based flow editor for creating event-driven automations.
"""

import os
import logging
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon

# Import from local modules
from Toolbar.core.plugin_system import Plugin
from Toolbar.core.config import Config

logger = logging.getLogger(__name__)

class EventsPlugin(Plugin):
    """Events plugin for the Toolbar application."""
    
    def __init__(self):
        """Initialize the Events plugin."""
        super().__init__()
        self.name = "Events"
        self.description = "Create event-driven automations with a visual node-based flow editor."
        self.version = "1.0.0"
        self.event_manager = None
        self.events_ui = None
        self.toolbar_button = None
        
    def initialize(self, config):
        """
        Initialize the Events plugin.
        
        Args:
            config: Configuration object
        """
        logger.info("Initializing Events plugin")
        
        # Create event manager
        try:
            from Toolbar.plugins.events.core.event_manager import EventManager
            self.event_manager = EventManager(config)
            
            # Create Events UI
            from Toolbar.plugins.events.ui.events_ui import EventsUI
            from Toolbar.main import get_toolbar_instance
            toolbar = get_toolbar_instance()
            if toolbar:
                self.events_ui = EventsUI(self.event_manager, toolbar)
                
                # Add Events button to the toolbar
                if hasattr(toolbar, 'toolbar'):
                    # Create Events button
                    self.toolbar_button = self.events_ui.events_button
                    
                    # Add button to the toolbar
                    toolbar.toolbar.addWidget(self.toolbar_button)
                    
                    # Connect button click to show Events dialog
                    self.toolbar_button.clicked.connect(self.events_ui.show_events_dialog)
                    
                    logger.info("Events button added to toolbar")
        except Exception as e:
            logger.error(f"Error initializing Events plugin: {e}")
            return False
        
        # Register event handlers for GitHub events
        try:
            from Toolbar.plugins.github.github.monitor import GitHubMonitor
            from Toolbar.main import get_plugin_instance
            
            github_plugin = get_plugin_instance("GitHub Integration")
            if github_plugin and hasattr(github_plugin, 'github_manager') and github_plugin.github_manager:
                github_monitor = github_plugin.github_manager.github_monitor
                if github_monitor:
                    # Connect GitHub webhook events to event manager
                    github_monitor.webhook_notification_received.connect(self._handle_github_notification)
                    logger.info("Connected to GitHub webhook events")
        except Exception as e:
            logger.warning(f"Could not connect to GitHub events: {e}")
        
        return True
    
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
        if notification.type == "pr":
            action = event_data.get('action', '')
            if action == 'opened' or action == 'reopened':
                event_type = "github_pr_created"
            elif action == 'synchronize':
                event_type = "github_pr_updated"
            elif action == 'closed' and event_data.get('pull_request', {}).get('merged', False):
                event_type = "github_pr_merged"
        elif notification.type == "branch":
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
    
    def get_icon(self):
        """Get the icon for the plugin to display in the taskbar."""
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "events.svg")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        return QIcon.fromTheme("flow-branch")
    
    def get_title(self):
        """Get the title for the plugin to display in the taskbar."""
        return "Events"
    
    def activate(self):
        """Activate the plugin when its taskbar button is clicked."""
        if self.events_ui:
            self.events_ui.show_events_dialog()
    
    def cleanup(self):
        """Clean up resources used by the plugin."""
        logger.info("Cleaning up Events plugin")
        if self.event_manager:
            self.event_manager.cleanup()
        return True
