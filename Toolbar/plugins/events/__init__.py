#!/usr/bin/env python3
import os
import sys
import logging
from PyQt5.QtGui import QIcon

from Toolbar.core.plugin_system import Plugin
from Toolbar.core.events.event_system import EventManager
from Toolbar.plugins.events.ui.event_system import EventSystemUI

logger = logging.getLogger(__name__)

class EventsPlugin(Plugin):
    """Plugin for event system with visual node flow editor."""
    
    def __init__(self):
        """Initialize the events plugin."""
        super().__init__()
        self.event_manager = None
        self.ui = None
    
    def initialize(self, config, event_bus=None, toolbar=None):
        """Initialize the plugin with the given configuration and event bus."""
        super().initialize(config, event_bus, toolbar)
        
        # Create event manager
        self.event_manager = EventManager(config)
        
        # Create UI
        self.ui = EventSystemUI(self.event_manager)
        
        logger.info("Events plugin initialized")
        return True
    
    def activate(self):
        """Activate the plugin."""
        super().activate()
        
        # Show the event manager dialog
        if self.ui:
            self.ui.open_event_manager()
        
        logger.info("Events plugin activated")
        return True
    
    def deactivate(self):
        """Deactivate the plugin."""
        super().deactivate()
        logger.info("Events plugin deactivated")
        return True
    
    def cleanup(self):
        """Clean up resources used by the plugin."""
        super().cleanup()
        logger.info("Events plugin cleaned up")
        return True
    
    def get_icon(self):
        """Get the icon for the plugin."""
        # Use a default icon if the custom icon is not available
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "events.svg")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        else:
            return QIcon.fromTheme("preferences-system")
    
    def get_title(self):
        """Get the title for the plugin."""
        return "Events"
    
    def get_settings_ui(self):
        """Get the settings UI for the plugin."""
        return self.ui
