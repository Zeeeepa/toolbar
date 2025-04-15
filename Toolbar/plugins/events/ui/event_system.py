#!/usr/bin/env python3
import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Type, Callable, Set, Union, Tuple

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QDialog, QMessageBox, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QIcon

from Toolbar.core.events.event_system import EventManager
from Toolbar.plugins.events.ui.events_ui import EventsDialog

logger = logging.getLogger(__name__)

class EventSystemUI(QWidget):
    """UI for the event system."""
    
    def __init__(self, event_manager, parent=None):
        """Initialize the event system UI."""
        super().__init__(parent)
        self.event_manager = event_manager
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create button to open event manager
        open_button = QPushButton("Open Event Manager")
        open_button.clicked.connect(self.open_event_manager)
        layout.addWidget(open_button)
        
        # Add status label
        self.status_label = QLabel()
        self.update_status_label()
        layout.addWidget(self.status_label)
        
        # Connect to event manager signals
        self.event_manager.event_triggered.connect(self.on_event_triggered)
        self.event_manager.action_executed.connect(self.on_action_executed)
    
    def open_event_manager(self):
        """Open the event manager dialog."""
        dialog = EventsDialog(self.event_manager, self)
        dialog.exec_()
        self.update_status_label()
    
    def update_status_label(self):
        """Update the status label with event count."""
        events = self.event_manager.get_all_events()
        active_events = [e for e in events if e.enabled]
        
        self.status_label.setText(f"Events: {len(events)} total, {len(active_events)} active")
    
    def on_event_triggered(self, event_type, data):
        """Handle event triggered signal."""
        logger.info(f"Event triggered: {event_type.value}")
        self.update_status_label()
    
    def on_action_executed(self, action, result):
        """Handle action executed signal."""
        logger.info(f"Action executed: {action.name}")
        self.update_status_label()
