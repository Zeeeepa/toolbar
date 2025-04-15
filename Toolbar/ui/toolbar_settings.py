#!/usr/bin/env python3
import os
import sys
import logging
from typing import Dict, List, Any, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTabWidget, QWidget, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QGroupBox, QRadioButton, QButtonGroup, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QSettings, QSize
from PyQt5.QtGui import QIcon, QFont

logger = logging.getLogger(__name__)

class ToolbarSettingsDialog(QDialog):
    """Dialog for toolbar settings."""
    
    def __init__(self, config, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        self.config = config
        
        self.setWindowTitle("Toolbar Settings")
        self.setMinimumSize(600, 400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Create general tab
        general_tab = QWidget()
        tab_widget.addTab(general_tab, "General")
        self._create_general_tab(general_tab)
        
        # Create appearance tab
        appearance_tab = QWidget()
        tab_widget.addTab(appearance_tab, "Appearance")
        self._create_appearance_tab(appearance_tab)
        
        # Create plugins tab
        plugins_tab = QWidget()
        tab_widget.addTab(plugins_tab, "Plugins")
        self._create_plugins_tab(plugins_tab)
        
        # Create locations tab
        locations_tab = QWidget()
        tab_widget.addTab(locations_tab, "Locations")
        self._create_locations_tab(locations_tab)
        
        # Create buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # Add save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        # Add cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # Load settings
        self.load_settings()
    
    def _create_general_tab(self, tab):
        """Create the general settings tab."""
        layout = QVBoxLayout(tab)
        
        # Create form layout
        form_layout = QFormLayout()
        layout.addLayout(form_layout)
        
        # Add auto start setting
        self.auto_start_checkbox = QCheckBox("Start on system boot")
        form_layout.addRow("Auto Start:", self.auto_start_checkbox)
        
        # Add minimize to tray setting
        self.minimize_to_tray_checkbox = QCheckBox("Minimize to system tray")
        form_layout.addRow("Minimize to Tray:", self.minimize_to_tray_checkbox)
        
        # Add stay on top setting
        self.stay_on_top_checkbox = QCheckBox("Keep toolbar on top of other windows")
        form_layout.addRow("Stay on Top:", self.stay_on_top_checkbox)
        
        # Add spacer
        layout.addStretch()
    
    def _create_appearance_tab(self, tab):
        """Create the appearance settings tab."""
        layout = QVBoxLayout(tab)
        
        # Create form layout
        form_layout = QFormLayout()
        layout.addLayout(form_layout)
        
        # Add position setting
        self.position_combo = QComboBox()
        self.position_combo.addItems(["Top", "Bottom", "Left", "Right"])
        form_layout.addRow("Position:", self.position_combo)
        
        # Add opacity setting
        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setRange(0.1, 1.0)
        self.opacity_spin.setSingleStep(0.1)
        self.opacity_spin.setDecimals(1)
        form_layout.addRow("Opacity:", self.opacity_spin)
        
        # Add theme setting
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        form_layout.addRow("Theme:", self.theme_combo)
        
        # Add spacer
        layout.addStretch()
    
    def _create_plugins_tab(self, tab):
        """Create the plugins settings tab."""
        layout = QVBoxLayout(tab)
        
        # Add enhanced plugin system setting
        self.enhanced_plugins_checkbox = QCheckBox("Use enhanced plugin system")
        self.enhanced_plugins_checkbox.setToolTip("Enable the enhanced plugin system with additional features")
        layout.addWidget(self.enhanced_plugins_checkbox)
        
        # Add auto-discovery setting
        self.auto_discovery_checkbox = QCheckBox("Enable plugin auto-discovery")
        self.auto_discovery_checkbox.setToolTip("Automatically discover and load plugins from plugin directories")
        layout.addWidget(self.auto_discovery_checkbox)
        
        # Add plugin directories section
        layout.addWidget(QLabel("Plugin Directories:"))
        
        # Create plugin directories list
        self.plugin_dirs_list = QListWidget()
        layout.addWidget(self.plugin_dirs_list)
        
        # Add plugin directory buttons
        dir_buttons_layout = QHBoxLayout()
        layout.addLayout(dir_buttons_layout)
        
        # Add add directory button
        add_dir_button = QPushButton("Add Directory")
        add_dir_button.clicked.connect(self._add_plugin_directory)
        dir_buttons_layout.addWidget(add_dir_button)
        
        # Add remove directory button
        remove_dir_button = QPushButton("Remove Directory")
        remove_dir_button.clicked.connect(self._remove_plugin_directory)
        dir_buttons_layout.addWidget(remove_dir_button)
        
        # Add spacer
        layout.addStretch()
    
    def _create_locations_tab(self, tab):
        """Create the locations settings tab."""
        layout = QVBoxLayout(tab)
        
        # Add locations table
        layout.addWidget(QLabel("Plugin Locations:"))
        
        # Create locations table
        self.locations_table = QTableWidget(0, 4)
        self.locations_table.setHorizontalHeaderLabels(["ID", "Name", "Path", "Enabled"])
        self.locations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.locations_table)
        
        # Add location buttons
        loc_buttons_layout = QHBoxLayout()
        layout.addLayout(loc_buttons_layout)
        
        # Add add location button
        add_loc_button = QPushButton("Add Location")
        add_loc_button.clicked.connect(self._add_location)
        loc_buttons_layout.addWidget(add_loc_button)
        
        # Add edit location button
        edit_loc_button = QPushButton("Edit Location")
        edit_loc_button.clicked.connect(self._edit_location)
        loc_buttons_layout.addWidget(edit_loc_button)
        
        # Add remove location button
        remove_loc_button = QPushButton("Remove Location")
        remove_loc_button.clicked.connect(self._remove_location)
        loc_buttons_layout.addWidget(remove_loc_button)
        
        # Add spacer
        layout.addStretch()
    
    def _add_plugin_directory(self):
        """Add a plugin directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Plugin Directory",
            os.path.expanduser("~")
        )
        
        if directory:
            # Check if directory already exists
            for i in range(self.plugin_dirs_list.count()):
                if self.plugin_dirs_list.item(i).text() == directory:
                    QMessageBox.warning(
                        self,
                        "Duplicate Directory",
                        f"Directory {directory} is already in the list."
                    )
                    return
            
            # Add directory to list
            self.plugin_dirs_list.addItem(directory)
    
    def _remove_plugin_directory(self):
        """Remove a plugin directory."""
        selected_items = self.plugin_dirs_list.selectedItems()
        if not selected_items:
            return
        
        # Remove selected items
        for item in selected_items:
            self.plugin_dirs_list.takeItem(self.plugin_dirs_list.row(item))
    
    def _add_location(self):
        """Add a plugin location."""
        # Create a dialog for location details
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Plugin Location")
        dialog.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout(dialog)
        
        # Create form layout
        form_layout = QFormLayout()
        layout.addLayout(form_layout)
        
        # Add ID field
        id_edit = QLineEdit()
        form_layout.addRow("ID:", id_edit)
        
        # Add name field
        name_edit = QLineEdit()
        form_layout.addRow("Name:", name_edit)
        
        # Add path field
        path_layout = QHBoxLayout()
        path_edit = QLineEdit()
        path_layout.addWidget(path_edit)
        
        # Add browse button
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(lambda: self._browse_location_path(path_edit))
        path_layout.addWidget(browse_button)
        
        form_layout.addRow("Path:", path_layout)
        
        # Add enabled checkbox
        enabled_checkbox = QCheckBox("Enabled")
        enabled_checkbox.setChecked(True)
        form_layout.addRow("", enabled_checkbox)
        
        # Add auto-discover checkbox
        auto_discover_checkbox = QCheckBox("Auto-discover plugins")
        auto_discover_checkbox.setChecked(True)
        form_layout.addRow("", auto_discover_checkbox)
        
        # Add priority field
        priority_spin = QSpinBox()
        priority_spin.setRange(1, 1000)
        priority_spin.setValue(100)
        form_layout.addRow("Priority:", priority_spin)
        
        # Add buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # Add OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_button)
        
        # Add cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        
        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            # Get values
            location_id = id_edit.text()
            name = name_edit.text()
            path = path_edit.text()
            enabled = enabled_checkbox.isChecked()
            auto_discover = auto_discover_checkbox.isChecked()
            priority = priority_spin.value()
            
            # Validate values
            if not location_id:
                QMessageBox.warning(self, "Validation Error", "ID is required")
                return
            
            if not name:
                QMessageBox.warning(self, "Validation Error", "Name is required")
                return
            
            if not path:
                QMessageBox.warning(self, "Validation Error", "Path is required")
                return
            
            # Check if ID already exists
            for row in range(self.locations_table.rowCount()):
                if self.locations_table.item(row, 0).text() == location_id:
                    QMessageBox.warning(
                        self,
                        "Duplicate ID",
                        f"Location ID {location_id} already exists."
                    )
                    return
            
            # Add location to table
            row = self.locations_table.rowCount()
            self.locations_table.insertRow(row)
            
            # Add ID cell
            id_item = QTableWidgetItem(location_id)
            self.locations_table.setItem(row, 0, id_item)
            
            # Add name cell
            name_item = QTableWidgetItem(name)
            self.locations_table.setItem(row, 1, name_item)
            
            # Add path cell
            path_item = QTableWidgetItem(path)
            self.locations_table.setItem(row, 2, path_item)
            
            # Add enabled cell
            enabled_item = QTableWidgetItem("Yes" if enabled else "No")
            self.locations_table.setItem(row, 3, enabled_item)
            
            # Store additional data
            id_item.setData(Qt.UserRole, {
                "id": location_id,
                "name": name,
                "path": path,
                "enabled": enabled,
                "auto_discover": auto_discover,
                "priority": priority
            })
    
    def _edit_location(self):
        """Edit a plugin location."""
        selected_items = self.locations_table.selectedItems()
        if not selected_items:
            return
        
        # Get the row
        row = selected_items[0].row()
        
        # Get the location data
        id_item = self.locations_table.item(row, 0)
        location_data = id_item.data(Qt.UserRole)
        
        # Create a dialog for location details
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Plugin Location")
        dialog.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout(dialog)
        
        # Create form layout
        form_layout = QFormLayout()
        layout.addLayout(form_layout)
        
        # Add ID field
        id_edit = QLineEdit(location_data["id"])
        id_edit.setReadOnly(True)  # ID cannot be changed
        form_layout.addRow("ID:", id_edit)
        
        # Add name field
        name_edit = QLineEdit(location_data["name"])
        form_layout.addRow("Name:", name_edit)
        
        # Add path field
        path_layout = QHBoxLayout()
        path_edit = QLineEdit(location_data["path"])
        path_layout.addWidget(path_edit)
        
        # Add browse button
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(lambda: self._browse_location_path(path_edit))
        path_layout.addWidget(browse_button)
        
        form_layout.addRow("Path:", path_layout)
        
        # Add enabled checkbox
        enabled_checkbox = QCheckBox("Enabled")
        enabled_checkbox.setChecked(location_data["enabled"])
        form_layout.addRow("", enabled_checkbox)
        
        # Add auto-discover checkbox
        auto_discover_checkbox = QCheckBox("Auto-discover plugins")
        auto_discover_checkbox.setChecked(location_data["auto_discover"])
        form_layout.addRow("", auto_discover_checkbox)
        
        # Add priority field
        priority_spin = QSpinBox()
        priority_spin.setRange(1, 1000)
        priority_spin.setValue(location_data["priority"])
        form_layout.addRow("Priority:", priority_spin)
        
        # Add buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # Add OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_button)
        
        # Add cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        
        # Show dialog
        if dialog.exec_() == QDialog.Accepted:
            # Get values
            name = name_edit.text()
            path = path_edit.text()
            enabled = enabled_checkbox.isChecked()
            auto_discover = auto_discover_checkbox.isChecked()
            priority = priority_spin.value()
            
            # Validate values
            if not name:
                QMessageBox.warning(self, "Validation Error", "Name is required")
                return
            
            if not path:
                QMessageBox.warning(self, "Validation Error", "Path is required")
                return
            
            # Update location in table
            name_item = self.locations_table.item(row, 1)
            name_item.setText(name)
            
            path_item = self.locations_table.item(row, 2)
            path_item.setText(path)
            
            enabled_item = self.locations_table.item(row, 3)
            enabled_item.setText("Yes" if enabled else "No")
            
            # Update additional data
            id_item.setData(Qt.UserRole, {
                "id": location_data["id"],
                "name": name,
                "path": path,
                "enabled": enabled,
                "auto_discover": auto_discover,
                "priority": priority
            })
    
    def _remove_location(self):
        """Remove a plugin location."""
        selected_items = self.locations_table.selectedItems()
        if not selected_items:
            return
        
        # Get the row
        row = selected_items[0].row()
        
        # Get the location ID
        location_id = self.locations_table.item(row, 0).text()
        
        # Confirm deletion
        if QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete location {location_id}?",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        
        # Remove the row
        self.locations_table.removeRow(row)
    
    def _browse_location_path(self, path_edit):
        """Browse for a location path."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Plugin Location Directory",
            path_edit.text() or os.path.expanduser("~")
        )
        
        if directory:
            path_edit.setText(directory)
    
    def load_settings(self):
        """Load settings from configuration."""
        # Load general settings
        self.auto_start_checkbox.setChecked(self.config.get_setting("auto_start", False))
        self.minimize_to_tray_checkbox.setChecked(self.config.get_setting("ui.minimize_to_tray", True))
        self.stay_on_top_checkbox.setChecked(self.config.get_setting("ui.stay_on_top", True))
        
        # Load appearance settings
        position = self.config.get_setting("ui.position", "top")
        self.position_combo.setCurrentText(position.capitalize())
        
        opacity = float(self.config.get_setting("ui.opacity", 0.9))
        self.opacity_spin.setValue(opacity)
        
        theme = self.config.get_setting("ui.theme", "System")
        self.theme_combo.setCurrentText(theme)
        
        # Load plugin settings
        self.enhanced_plugins_checkbox.setChecked(self.config.get_setting("plugins.use_enhanced", True))
        self.auto_discovery_checkbox.setChecked(self.config.get_setting("plugins.auto_discovery", True))
        
        # Load plugin directories
        plugin_dirs = self.config.get_setting("plugins.directories", [])
        self.plugin_dirs_list.clear()
        for directory in plugin_dirs:
            self.plugin_dirs_list.addItem(directory)
        
        # Load plugin locations
        locations = self.config.get_setting("plugins.locations", [])
        self.locations_table.setRowCount(0)
        for location in locations:
            row = self.locations_table.rowCount()
            self.locations_table.insertRow(row)
            
            # Add ID cell
            id_item = QTableWidgetItem(location.get("id", ""))
            self.locations_table.setItem(row, 0, id_item)
            
            # Add name cell
            name_item = QTableWidgetItem(location.get("name", ""))
            self.locations_table.setItem(row, 1, name_item)
            
            # Add path cell
            path_item = QTableWidgetItem(location.get("path", ""))
            self.locations_table.setItem(row, 2, path_item)
            
            # Add enabled cell
            enabled_item = QTableWidgetItem("Yes" if location.get("enabled", True) else "No")
            self.locations_table.setItem(row, 3, enabled_item)
            
            # Store additional data
            id_item.setData(Qt.UserRole, location)
    
    def save_settings(self):
        """Save settings to configuration."""
        # Save general settings
        self.config.set_setting("auto_start", self.auto_start_checkbox.isChecked())
        self.config.set_setting("ui.minimize_to_tray", self.minimize_to_tray_checkbox.isChecked())
        self.config.set_setting("ui.stay_on_top", self.stay_on_top_checkbox.isChecked())
        
        # Save appearance settings
        position = self.position_combo.currentText().lower()
        self.config.set_setting("ui.position", position)
        
        opacity = self.opacity_spin.value()
        self.config.set_setting("ui.opacity", opacity)
        
        theme = self.theme_combo.currentText()
        self.config.set_setting("ui.theme", theme)
        
        # Save plugin settings
        self.config.set_setting("plugins.use_enhanced", self.enhanced_plugins_checkbox.isChecked())
        self.config.set_setting("plugins.auto_discovery", self.auto_discovery_checkbox.isChecked())
        
        # Save plugin directories
        plugin_dirs = []
        for i in range(self.plugin_dirs_list.count()):
            plugin_dirs.append(self.plugin_dirs_list.item(i).text())
        self.config.set_setting("plugins.directories", plugin_dirs)
        
        # Save plugin locations
        locations = []
        for row in range(self.locations_table.rowCount()):
            id_item = self.locations_table.item(row, 0)
            location_data = id_item.data(Qt.UserRole)
            locations.append(location_data)
        self.config.set_setting("plugins.locations", locations)
        
        # Save configuration
        self.config.save()
        
        # Accept dialog
        self.accept()
