#!/usr/bin/env python3
import os
import sys
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Type, Callable, Set, Union, Tuple

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTabWidget, QWidget, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QGroupBox, QRadioButton, QButtonGroup, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QSplitter, QTreeWidget, QTreeWidgetItem, QMenu, QAction,
    QToolButton, QScrollArea, QFrame, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, QSettings, QSize, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette

from Toolbar.core.events.event_system import (
    EventManager, Event, EventTrigger, Action, Condition, ActionParameter,
    EventType, ActionType
)
from Toolbar.plugins.events.ui.node_flow_editor import NodeFlowEditorDialog

logger = logging.getLogger(__name__)

class EventsDialog(QDialog):
    """Dialog for managing events."""
    
    def __init__(self, event_manager, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        self.event_manager = event_manager
        
        self.setWindowTitle("Event Manager")
        self.setMinimumSize(800, 600)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Create events list
        events_widget = QWidget()
        events_layout = QVBoxLayout(events_widget)
        events_layout.setContentsMargins(0, 0, 0, 0)
        
        events_label = QLabel("Events")
        events_label.setFont(QFont("Arial", 12, QFont.Bold))
        events_layout.addWidget(events_label)
        
        self.events_list = QListWidget()
        self.events_list.setSelectionMode(QListWidget.SingleSelection)
        self.events_list.currentItemChanged.connect(self._on_event_selected)
        events_layout.addWidget(self.events_list)
        
        # Add events buttons
        events_buttons_layout = QHBoxLayout()
        events_layout.addLayout(events_buttons_layout)
        
        add_event_button = QPushButton("Add Event")
        add_event_button.clicked.connect(self._add_event)
        events_buttons_layout.addWidget(add_event_button)
        
        remove_event_button = QPushButton("Remove Event")
        remove_event_button.clicked.connect(self._remove_event)
        events_buttons_layout.addWidget(remove_event_button)
        
        # Add visual editor button
        visual_editor_button = QPushButton("Visual Flow Editor")
        visual_editor_button.clicked.connect(self._open_visual_editor)
        events_buttons_layout.addWidget(visual_editor_button)
        
        # Add events widget to splitter
        splitter.addWidget(events_widget)
        
        # Create event details widget
        self.event_details_widget = QWidget()
        event_details_layout = QVBoxLayout(self.event_details_widget)
        event_details_layout.setContentsMargins(0, 0, 0, 0)
        
        event_details_label = QLabel("Event Details")
        event_details_label.setFont(QFont("Arial", 12, QFont.Bold))
        event_details_layout.addWidget(event_details_label)
        
        # Create form layout for event details
        form_layout = QFormLayout()
        event_details_layout.addLayout(form_layout)
        
        # Add event name field
        self.event_name_edit = QLineEdit()
        form_layout.addRow("Name:", self.event_name_edit)
        
        # Add event description field
        self.event_description_edit = QTextEdit()
        self.event_description_edit.setMaximumHeight(100)
        form_layout.addRow("Description:", self.event_description_edit)
        
        # Add event enabled checkbox
        self.event_enabled_checkbox = QCheckBox("Enabled")
        form_layout.addRow("", self.event_enabled_checkbox)
        
        # Create tab widget for trigger and actions
        tab_widget = QTabWidget()
        event_details_layout.addWidget(tab_widget)
        
        # Create trigger tab
        trigger_tab = QWidget()
        tab_widget.addTab(trigger_tab, "Trigger")
        self._create_trigger_tab(trigger_tab)
        
        # Create actions tab
        actions_tab = QWidget()
        tab_widget.addTab(actions_tab, "Actions")
        self._create_actions_tab(actions_tab)
        
        # Add save button
        save_button = QPushButton("Save Event")
        save_button.clicked.connect(self._save_event)
        event_details_layout.addWidget(save_button)
        
        # Add event details widget to splitter
        splitter.addWidget(self.event_details_widget)
        
        # Set splitter sizes
        splitter.setSizes([200, 600])
        
        # Add dialog buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        # Initialize UI
        self._load_events()
        
        # Disable event details until an event is selected
        self.event_details_widget.setEnabled(False)
    
    def _create_trigger_tab(self, tab):
        """Create the trigger tab."""
        layout = QVBoxLayout(tab)
        
        # Create form layout for trigger details
        form_layout = QFormLayout()
        layout.addLayout(form_layout)
        
        # Add trigger name field
        self.trigger_name_edit = QLineEdit()
        form_layout.addRow("Name:", self.trigger_name_edit)
        
        # Add trigger type combo
        self.trigger_type_combo = QComboBox()
        for event_type in EventType:
            self.trigger_type_combo.addItem(event_type.value, event_type)
        form_layout.addRow("Type:", self.trigger_type_combo)
        
        # Add trigger enabled checkbox
        self.trigger_enabled_checkbox = QCheckBox("Enabled")
        form_layout.addRow("", self.trigger_enabled_checkbox)
        
        # Add conditions section
        conditions_group = QGroupBox("Conditions")
        layout.addWidget(conditions_group)
        
        conditions_layout = QVBoxLayout(conditions_group)
        
        # Add conditions list
        self.conditions_table = QTableWidget(0, 3)
        self.conditions_table.setHorizontalHeaderLabels(["Field", "Operator", "Value"])
        self.conditions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        conditions_layout.addWidget(self.conditions_table)
        
        # Add conditions buttons
        conditions_buttons_layout = QHBoxLayout()
        conditions_layout.addLayout(conditions_buttons_layout)
        
        add_condition_button = QPushButton("Add Condition")
        add_condition_button.clicked.connect(self._add_condition)
        conditions_buttons_layout.addWidget(add_condition_button)
        
        remove_condition_button = QPushButton("Remove Condition")
        remove_condition_button.clicked.connect(self._remove_condition)
        conditions_buttons_layout.addWidget(remove_condition_button)
    
    def _create_actions_tab(self, tab):
        """Create the actions tab."""
        layout = QVBoxLayout(tab)
        
        # Add actions list
        self.actions_list = QListWidget()
        self.actions_list.setSelectionMode(QListWidget.SingleSelection)
        self.actions_list.currentItemChanged.connect(self._on_action_selected)
        layout.addWidget(self.actions_list)
        
        # Add actions buttons
        actions_buttons_layout = QHBoxLayout()
        layout.addLayout(actions_buttons_layout)
        
        add_action_button = QPushButton("Add Action")
        add_action_button.clicked.connect(self._add_action)
        actions_buttons_layout.addWidget(add_action_button)
        
        remove_action_button = QPushButton("Remove Action")
        remove_action_button.clicked.connect(self._remove_action)
        actions_buttons_layout.addWidget(remove_action_button)
        
        # Add action details section
        self.action_details_group = QGroupBox("Action Details")
        layout.addWidget(self.action_details_group)
        
        action_details_layout = QVBoxLayout(self.action_details_group)
        
        # Create form layout for action details
        form_layout = QFormLayout()
        action_details_layout.addLayout(form_layout)
        
        # Add action name field
        self.action_name_edit = QLineEdit()
        form_layout.addRow("Name:", self.action_name_edit)
        
        # Add action type combo
        self.action_type_combo = QComboBox()
        for action_type in ActionType:
            self.action_type_combo.addItem(action_type.value, action_type)
        self.action_type_combo.currentIndexChanged.connect(self._on_action_type_changed)
        form_layout.addRow("Type:", self.action_type_combo)
        
        # Add action enabled checkbox
        self.action_enabled_checkbox = QCheckBox("Enabled")
        form_layout.addRow("", self.action_enabled_checkbox)
        
        # Add parameters section
        parameters_group = QGroupBox("Parameters")
        action_details_layout.addWidget(parameters_group)
        
        parameters_layout = QVBoxLayout(parameters_group)
        
        # Add parameters list
        self.parameters_table = QTableWidget(0, 2)
        self.parameters_table.setHorizontalHeaderLabels(["Name", "Value"])
        self.parameters_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        parameters_layout.addWidget(self.parameters_table)
        
        # Add parameters buttons
        parameters_buttons_layout = QHBoxLayout()
        parameters_layout.addLayout(parameters_buttons_layout)
        
        add_parameter_button = QPushButton("Add Parameter")
        add_parameter_button.clicked.connect(self._add_parameter)
        parameters_buttons_layout.addWidget(add_parameter_button)
        
        remove_parameter_button = QPushButton("Remove Parameter")
        remove_parameter_button.clicked.connect(self._remove_parameter)
        parameters_buttons_layout.addWidget(remove_parameter_button)
        
        # Add save action button
        save_action_button = QPushButton("Save Action")
        save_action_button.clicked.connect(self._save_action)
        action_details_layout.addWidget(save_action_button)
        
        # Disable action details until an action is selected
        self.action_details_group.setEnabled(False)
    
    def _load_events(self):
        """Load events from the event manager."""
        # Clear the list
        self.events_list.clear()
        
        # Add events to the list
        for event in self.event_manager.get_all_events():
            item = QListWidgetItem(event.name)
            item.setData(Qt.UserRole, event.id)
            self.events_list.addItem(item)
    
    def _on_event_selected(self, current, previous):
        """Handle event selection."""
        if current:
            # Enable event details
            self.event_details_widget.setEnabled(True)
            
            # Get the event
            event_id = current.data(Qt.UserRole)
            event = self.event_manager.get_event(event_id)
            
            if event:
                # Update event details
                self.event_name_edit.setText(event.name)
                self.event_description_edit.setText(event.description)
                self.event_enabled_checkbox.setChecked(event.enabled)
                
                # Update trigger details
                self.trigger_name_edit.setText(event.trigger.name)
                index = self.trigger_type_combo.findData(event.trigger.event_type)
                if index >= 0:
                    self.trigger_type_combo.setCurrentIndex(index)
                self.trigger_enabled_checkbox.setChecked(event.trigger.enabled)
                
                # Update conditions
                self.conditions_table.setRowCount(0)
                for condition in event.trigger.conditions:
                    row = self.conditions_table.rowCount()
                    self.conditions_table.insertRow(row)
                    
                    field_item = QTableWidgetItem(condition.field)
                    self.conditions_table.setItem(row, 0, field_item)
                    
                    operator_item = QTableWidgetItem(condition.operator)
                    self.conditions_table.setItem(row, 1, operator_item)
                    
                    value_item = QTableWidgetItem(str(condition.value))
                    self.conditions_table.setItem(row, 2, value_item)
                
                # Update actions
                self.actions_list.clear()
                for action in event.actions:
                    item = QListWidgetItem(action.name)
                    item.setData(Qt.UserRole, action.id)
                    self.actions_list.addItem(item)
                
                # Disable action details
                self.action_details_group.setEnabled(False)
        else:
            # Disable event details
            self.event_details_widget.setEnabled(False)
    
    def _on_action_selected(self, current, previous):
        """Handle action selection."""
        if current:
            # Enable action details
            self.action_details_group.setEnabled(True)
            
            # Get the event and action
            event_item = self.events_list.currentItem()
            if not event_item:
                return
            
            event_id = event_item.data(Qt.UserRole)
            event = self.event_manager.get_event(event_id)
            
            if not event:
                return
            
            action_id = current.data(Qt.UserRole)
            action = next((a for a in event.actions if a.id == action_id), None)
            
            if action:
                # Update action details
                self.action_name_edit.setText(action.name)
                index = self.action_type_combo.findData(action.action_type)
                if index >= 0:
                    self.action_type_combo.setCurrentIndex(index)
                self.action_enabled_checkbox.setChecked(action.enabled)
                
                # Update parameters
                self.parameters_table.setRowCount(0)
                for parameter in action.parameters:
                    row = self.parameters_table.rowCount()
                    self.parameters_table.insertRow(row)
                    
                    name_item = QTableWidgetItem(parameter.name)
                    self.parameters_table.setItem(row, 0, name_item)
                    
                    value_item = QTableWidgetItem(str(parameter.value))
                    self.parameters_table.setItem(row, 1, value_item)
        else:
            # Disable action details
            self.action_details_group.setEnabled(False)
    
    def _on_action_type_changed(self, index):
        """Handle action type change."""
        action_type = self.action_type_combo.itemData(index)
        
        # Clear parameters
        self.parameters_table.setRowCount(0)
        
        # Add default parameters based on action type
        if action_type == ActionType.SEND_PROMPT:
            self._add_default_parameter("prompt_template", "")
            self._add_default_parameter("target", "clipboard")
        elif action_type == ActionType.CREATE_LINEAR_ISSUE:
            self._add_default_parameter("team_id", "")
            self._add_default_parameter("title_template", "")
            self._add_default_parameter("description_template", "")
        elif action_type == ActionType.AUTO_MERGE_PR:
            self._add_default_parameter("repo", "")
            self._add_default_parameter("pr_number", "")
        elif action_type == ActionType.RUN_SCRIPT:
            self._add_default_parameter("script_id", "")
    
    def _add_default_parameter(self, name, value):
        """Add a default parameter to the parameters table."""
        row = self.parameters_table.rowCount()
        self.parameters_table.insertRow(row)
        
        name_item = QTableWidgetItem(name)
        self.parameters_table.setItem(row, 0, name_item)
        
        value_item = QTableWidgetItem(str(value))
        self.parameters_table.setItem(row, 1, value_item)
    
    def _add_event(self):
        """Add a new event."""
        # Create a new event
        event_id = str(uuid.uuid4())
        trigger_id = str(uuid.uuid4())
        
        trigger = EventTrigger(
            id=trigger_id,
            name="New Trigger",
            event_type=EventType.CUSTOM,
            conditions=[],
            enabled=True
        )
        
        event = Event(
            id=event_id,
            name="New Event",
            description="",
            trigger=trigger,
            actions=[],
            enabled=True
        )
        
        # Add to event manager
        self.event_manager.add_event(event)
        
        # Add to list
        item = QListWidgetItem(event.name)
        item.setData(Qt.UserRole, event.id)
        self.events_list.addItem(item)
        self.events_list.setCurrentItem(item)
    
    def _remove_event(self):
        """Remove the selected event."""
        current_item = self.events_list.currentItem()
        if not current_item:
            return
        
        event_id = current_item.data(Qt.UserRole)
        
        # Confirm deletion
        if QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete this event?",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        
        # Remove from event manager
        self.event_manager.delete_event(event_id)
        
        # Remove from list
        self.events_list.takeItem(self.events_list.row(current_item))
        
        # Disable event details
        self.event_details_widget.setEnabled(False)
    
    def _save_event(self):
        """Save the current event."""
        current_item = self.events_list.currentItem()
        if not current_item:
            return
        
        event_id = current_item.data(Qt.UserRole)
        event = self.event_manager.get_event(event_id)
        
        if not event:
            return
        
        # Update event details
        event.name = self.event_name_edit.text()
        event.description = self.event_description_edit.toPlainText()
        event.enabled = self.event_enabled_checkbox.isChecked()
        
        # Update trigger details
        event.trigger.name = self.trigger_name_edit.text()
        event.trigger.event_type = self.trigger_type_combo.currentData()
        event.trigger.enabled = self.trigger_enabled_checkbox.isChecked()
        
        # Update conditions
        event.trigger.conditions = []
        for row in range(self.conditions_table.rowCount()):
            field = self.conditions_table.item(row, 0).text()
            operator = self.conditions_table.item(row, 1).text()
            value = self.conditions_table.item(row, 2).text()
            
            condition = Condition(field=field, operator=operator, value=value)
            event.trigger.conditions.append(condition)
        
        # Save to event manager
        self.event_manager.update_event(event_id, event)
        
        # Update list item
        current_item.setText(event.name)
        
        QMessageBox.information(self, "Event Saved", "Event saved successfully.")
    
    def _add_condition(self):
        """Add a new condition."""
        row = self.conditions_table.rowCount()
        self.conditions_table.insertRow(row)
        
        field_item = QTableWidgetItem("")
        self.conditions_table.setItem(row, 0, field_item)
        
        operator_item = QTableWidgetItem("equals")
        self.conditions_table.setItem(row, 1, operator_item)
        
        value_item = QTableWidgetItem("")
        self.conditions_table.setItem(row, 2, value_item)
    
    def _remove_condition(self):
        """Remove the selected condition."""
        selected_items = self.conditions_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        self.conditions_table.removeRow(row)
    
    def _add_action(self):
        """Add a new action."""
        current_item = self.events_list.currentItem()
        if not current_item:
            return
        
        event_id = current_item.data(Qt.UserRole)
        event = self.event_manager.get_event(event_id)
        
        if not event:
            return
        
        # Create a new action
        action_id = str(uuid.uuid4())
        
        action = Action(
            id=action_id,
            name="New Action",
            action_type=ActionType.CUSTOM,
            parameters=[],
            enabled=True
        )
        
        # Add to event
        event.actions.append(action)
        
        # Save to event manager
        self.event_manager.update_event(event_id, event)
        
        # Add to list
        item = QListWidgetItem(action.name)
        item.setData(Qt.UserRole, action.id)
        self.actions_list.addItem(item)
        self.actions_list.setCurrentItem(item)
    
    def _remove_action(self):
        """Remove the selected action."""
        current_event_item = self.events_list.currentItem()
        current_action_item = self.actions_list.currentItem()
        
        if not current_event_item or not current_action_item:
            return
        
        event_id = current_event_item.data(Qt.UserRole)
        event = self.event_manager.get_event(event_id)
        
        if not event:
            return
        
        action_id = current_action_item.data(Qt.UserRole)
        
        # Confirm deletion
        if QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete this action?",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        
        # Remove from event
        event.actions = [a for a in event.actions if a.id != action_id]
        
        # Save to event manager
        self.event_manager.update_event(event_id, event)
        
        # Remove from list
        self.actions_list.takeItem(self.actions_list.row(current_action_item))
        
        # Disable action details
        self.action_details_group.setEnabled(False)
    
    def _save_action(self):
        """Save the current action."""
        current_event_item = self.events_list.currentItem()
        current_action_item = self.actions_list.currentItem()
        
        if not current_event_item or not current_action_item:
            return
        
        event_id = current_event_item.data(Qt.UserRole)
        event = self.event_manager.get_event(event_id)
        
        if not event:
            return
        
        action_id = current_action_item.data(Qt.UserRole)
        action = next((a for a in event.actions if a.id == action_id), None)
        
        if not action:
            return
        
        # Update action details
        action.name = self.action_name_edit.text()
        action.action_type = self.action_type_combo.currentData()
        action.enabled = self.action_enabled_checkbox.isChecked()
        
        # Update parameters
        action.parameters = []
        for row in range(self.parameters_table.rowCount()):
            name = self.parameters_table.item(row, 0).text()
            value = self.parameters_table.item(row, 1).text()
            
            parameter = ActionParameter(name=name, value=value)
            action.parameters.append(parameter)
        
        # Save to event manager
        self.event_manager.update_event(event_id, event)
        
        # Update list item
        current_action_item.setText(action.name)
        
        QMessageBox.information(self, "Action Saved", "Action saved successfully.")
    
    def _add_parameter(self):
        """Add a new parameter."""
        row = self.parameters_table.rowCount()
        self.parameters_table.insertRow(row)
        
        name_item = QTableWidgetItem("")
        self.parameters_table.setItem(row, 0, name_item)
        
        value_item = QTableWidgetItem("")
        self.parameters_table.setItem(row, 1, value_item)
    
    def _remove_parameter(self):
        """Remove the selected parameter."""
        selected_items = self.parameters_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        self.parameters_table.removeRow(row)
    
    def _open_visual_editor(self):
        """Open the visual flow editor."""
        # Get the current event
        current_item = self.events_list.currentItem()
        event = None
        
        if current_item:
            event_id = current_item.data(Qt.UserRole)
            event = self.event_manager.get_event(event_id)
        
        # Create and show the node flow editor dialog
        dialog = NodeFlowEditorDialog(self.event_manager, self)
        
        # If we have a current event, load it
        if event:
            dialog.editor.current_event = event
            dialog.editor.event_name_edit.setText(event.name)
            dialog.editor.event_description_edit.setText(event.description)
            dialog.editor.event_enabled_checkbox.setChecked(event.enabled)
        
        # Show the dialog
        if dialog.exec_():
            # Reload events after dialog is closed
            self._load_events()
