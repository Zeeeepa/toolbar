#!/usr/bin/env python3
import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Type, Callable, Set, Union, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTabWidget, QFormLayout, QLineEdit, QTextEdit, QCheckBox, QGroupBox,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QMessageBox, QMenu, QAction, QToolButton, QSplitter, QFrame,
    QScrollArea, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, QSettings, QSize, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette

# Import event system
from Toolbar.plugins.events.core.event_system import (
    EventManager, Event, EventTrigger, Action, Condition, ActionParameter,
    EventType, ActionType
)

# Import node editor
from Toolbar.plugins.events.ui.node_editor import NodeEditorDialog
from Toolbar.plugins.events.ui.node_flow_editor import EnhancedNodeEditorDialog

logger = logging.getLogger(__name__)

class EventsUIIntegration:
    """Integration class for the Events UI with the enhanced node flow editor."""
    
    def __init__(self, events_ui):
        """Initialize the integration."""
        self.events_ui = events_ui
        self.event_manager = events_ui.event_manager
        
        # Add enhanced node editor button to events dialog
        self.add_enhanced_node_editor_button()
    
    def add_enhanced_node_editor_button(self):
        """Add enhanced node editor button to events dialog."""
        if hasattr(self.events_ui, 'events_dialog') and self.events_ui.events_dialog:
            # Get the events dialog
            dialog = self.events_ui.events_dialog
            
            # Check if the dialog has a button layout
            if hasattr(dialog, 'button_layout'):
                # Create enhanced node editor button
                self.enhanced_node_editor_button = QPushButton("Enhanced Flow Editor")
                self.enhanced_node_editor_button.clicked.connect(self.show_enhanced_node_editor)
                
                # Add button to layout
                dialog.button_layout.addWidget(self.enhanced_node_editor_button)
    
    def show_enhanced_node_editor(self):
        """Show the enhanced node editor dialog."""
        # Create enhanced node editor dialog
        dialog = EnhancedNodeEditorDialog(self.event_manager, self.events_ui.parent)
        
        # Show dialog
        dialog.exec_()
