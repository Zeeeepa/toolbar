import os
import json
import warnings
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                           QPushButton, QCheckBox, QMessageBox, QTabWidget, 
                           QWidget, QListWidget, QListWidgetItem, QTextEdit, 
                           QComboBox, QGroupBox, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap

from Toolbar.core.linear_integration import LinearIntegration, LinearIssue

# Suppress PyQt5 deprecation warnings
warnings.filterwarnings("ignore", message=".*sipPyTypeDict.*")

class LinearSettingsDialog(QDialog):
    """
    Dialog for configuring Linear API settings.
    """
    def __init__(self, linear_integration, parent=None):
        """
        Initialize the Linear settings dialog.
        
        Args:
            linear_integration (LinearIntegration): Linear integration instance
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.linear_integration = linear_integration
        
        # Set up the UI
        self.init_ui()
        
        # Apply dark theme
        self.apply_dark_theme()
        
        # Load settings
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Linear Settings")
        self.setMinimumSize(500, 350)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create API settings tab
        self.api_tab = QWidget()
        self.tab_widget.addTab(self.api_tab, "API Settings")
        
        # Create templates tab
        self.templates_tab = QWidget()
        self.tab_widget.addTab(self.templates_tab, "Issue Templates")
        
        # Set up API settings tab
        self.setup_api_tab()
        
        # Set up templates tab
        self.setup_templates_tab()
        
        # Create buttons
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        
        # Add spacer
        button_layout.addStretch()
        
        # Create Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        # Create Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
    
    def setup_api_tab(self):
        """Set up the API settings tab."""
        layout = QVBoxLayout(self.api_tab)
        
        # Create form layout
        form_layout = QFormLayout()
        layout.addLayout(form_layout)
        
        # Create API key input
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("API Key:", self.api_key_input)
        
        # Create team selection
        self.team_combo = QComboBox()
        form_layout.addRow("Default Team:", self.team_combo)
        
        # Create state selection
        self.state_combo = QComboBox()
        form_layout.addRow("Default State:", self.state_combo)
        
        # Create template selection
        self.template_combo = QComboBox()
        form_layout.addRow("Default Template:", self.template_combo)
        
        # Create test connection button
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        layout.addWidget(self.test_button)
        
        # Connect team combo box to update states
        self.team_combo.currentIndexChanged.connect(self.update_states)
    
    def setup_templates_tab(self):
        """Set up the templates tab."""
        layout = QVBoxLayout(self.templates_tab)
        
        # Create templates list
        self.templates_list = QListWidget()
        self.templates_list.currentRowChanged.connect(self.template_selected)
        layout.addWidget(self.templates_list)
        
        # Create template editor
        template_editor_layout = QVBoxLayout()
        layout.addLayout(template_editor_layout)
        
        # Create template name input
        name_layout = QHBoxLayout()
        template_editor_layout.addLayout(name_layout)
        
        name_layout.addWidget(QLabel("Name:"))
        self.template_name_input = QLineEdit()
        name_layout.addWidget(self.template_name_input)
        
        # Create template content editor
        template_editor_layout.addWidget(QLabel("Content:"))
        self.template_content_editor = QTextEdit()
        template_editor_layout.addWidget(self.template_content_editor)
        
        # Create template buttons
        template_buttons_layout = QHBoxLayout()
        template_editor_layout.addLayout(template_buttons_layout)
        
        # Create Add button
        self.add_template_button = QPushButton("Add")
        self.add_template_button.clicked.connect(self.add_template)
        template_buttons_layout.addWidget(self.add_template_button)
        
        # Create Update button
        self.update_template_button = QPushButton("Update")
        self.update_template_button.clicked.connect(self.update_template)
        self.update_template_button.setEnabled(False)
        template_buttons_layout.addWidget(self.update_template_button)
        
        # Create Remove button
        self.remove_template_button = QPushButton("Remove")
        self.remove_template_button.clicked.connect(self.remove_template)
        self.remove_template_button.setEnabled(False)
        template_buttons_layout.addWidget(self.remove_template_button)
    
    def load_settings(self):
        """Load settings from Linear integration."""
        # Load API key
        self.api_key_input.setText(self.linear_integration.api_key)
        
        # Load teams
        self.load_teams()
        
        # Load templates
        self.load_templates()
    
    def load_teams(self):
        """Load teams from Linear API."""
        if not self.linear_integration.api_key:
            return
        
        # Clear team combo box
        self.team_combo.clear()
        
        # Add empty option
        self.team_combo.addItem("", "")
        
        # Get teams
        teams = self.linear_integration.get_teams()
        
        # Add teams to combo box
        for team in teams:
            self.team_combo.addItem(f"{team['name']} ({team['key']})", team['id'])
        
        # Set current team
        default_team_id = self.linear_integration.settings.get("default_team_id", "")
        for i in range(self.team_combo.count()):
            if self.team_combo.itemData(i) == default_team_id:
                self.team_combo.setCurrentIndex(i)
                break
        
        # Update states
        self.update_states()
    
    def update_states(self):
        """Update states based on selected team."""
        # Clear state combo box
        self.state_combo.clear()
        
        # Add empty option
        self.state_combo.addItem("", "")
        
        # Get team ID
        team_id = self.team_combo.currentData()
        if not team_id:
            return
        
        # Get states
        states = self.linear_integration.get_states(team_id)
        
        # Add states to combo box
        for state in states:
            self.state_combo.addItem(state['name'], state['id'])
        
        # Set current state
        default_state_id = self.linear_integration.settings.get("default_state_id", "")
        for i in range(self.state_combo.count()):
            if self.state_combo.itemData(i) == default_state_id:
                self.state_combo.setCurrentIndex(i)
                break
    
    def load_templates(self):
        """Load templates from Linear integration."""
        # Clear templates list
        self.templates_list.clear()
        
        # Get templates
        templates = self.linear_integration.get_templates()
        
        # Add templates to list
        for template in templates:
            item = QListWidgetItem(template['name'])
            item.setData(Qt.UserRole, template)
            self.templates_list.addItem(item)
        
        # Clear template editor
        self.template_name_input.clear()
        self.template_content_editor.clear()
        self.update_template_button.setEnabled(False)
        self.remove_template_button.setEnabled(False)
        
        # Update template combo box
        self.template_combo.clear()
        self.template_combo.addItem("", "")
        for template in templates:
            self.template_combo.addItem(template['name'], template['name'])
        
        # Set current template
        default_template = self.linear_integration.settings.get("default_template", "")
        for i in range(self.template_combo.count()):
            if self.template_combo.itemData(i) == default_template:
                self.template_combo.setCurrentIndex(i)
                break
    
    def template_selected(self, row):
        """
        Handle template selection.
        
        Args:
            row (int): Selected row
        """
        if row < 0:
            # Clear template editor
            self.template_name_input.clear()
            self.template_content_editor.clear()
            self.update_template_button.setEnabled(False)
            self.remove_template_button.setEnabled(False)
            return
        
        # Get template
        item = self.templates_list.item(row)
        template = item.data(Qt.UserRole)
        
        # Update template editor
        self.template_name_input.setText(template['name'])
        self.template_content_editor.setText(template['content'])
        self.update_template_button.setEnabled(True)
        self.remove_template_button.setEnabled(True)
    
    def add_template(self):
        """Add a new template."""
        name = self.template_name_input.text().strip()
        content = self.template_content_editor.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "Invalid Template", "Template name cannot be empty.")
            return
        
        if not content:
            QMessageBox.warning(self, "Invalid Template", "Template content cannot be empty.")
            return
        
        # Check for duplicate name
        for i in range(self.templates_list.count()):
            item = self.templates_list.item(i)
            template = item.data(Qt.UserRole)
            if template['name'] == name:
                QMessageBox.warning(self, "Duplicate Template", f"Template '{name}' already exists.")
                return
        
        # Add template
        if self.linear_integration.add_template(name, content):
            # Reload templates
            self.load_templates()
            
            # Clear template editor
            self.template_name_input.clear()
            self.template_content_editor.clear()
        else:
            QMessageBox.warning(self, "Error", "Failed to add template.")
    
    def update_template(self):
        """Update the selected template."""
        row = self.templates_list.currentRow()
        if row < 0:
            return
        
        name = self.template_name_input.text().strip()
        content = self.template_content_editor.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "Invalid Template", "Template name cannot be empty.")
            return
        
        if not content:
            QMessageBox.warning(self, "Invalid Template", "Template content cannot be empty.")
            return
        
        # Check for duplicate name
        for i in range(self.templates_list.count()):
            if i == row:
                continue
            
            item = self.templates_list.item(i)
            template = item.data(Qt.UserRole)
            if template['name'] == name:
                QMessageBox.warning(self, "Duplicate Template", f"Template '{name}' already exists.")
                return
        
        # Update template
        if self.linear_integration.update_template(row, name, content):
            # Reload templates
            self.load_templates()
            
            # Select the updated template
            self.templates_list.setCurrentRow(row)
        else:
            QMessageBox.warning(self, "Error", "Failed to update template.")
    
    def remove_template(self):
        """Remove the selected template."""
        row = self.templates_list.currentRow()
        if row < 0:
            return
        
        # Get template name
        item = self.templates_list.item(row)
        template = item.data(Qt.UserRole)
        name = template['name']
        
        # Confirm removal
        confirm = QMessageBox.question(
            self, "Confirm Removal", 
            f"Are you sure you want to remove template '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Remove template
            if self.linear_integration.remove_template(row):
                # Reload templates
                self.load_templates()
            else:
                QMessageBox.warning(self, "Error", "Failed to remove template.")
    
    def test_connection(self):
        """Test the Linear API connection."""
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, "Invalid API Key", "API key cannot be empty.")
            return
        
        # Set API key
        self.linear_integration.set_api_key(api_key)
        
        # Test connection
        teams = self.linear_integration.get_teams()
        
        if teams:
            QMessageBox.information(self, "Connection Successful", "Successfully connected to Linear API.")
            
            # Load teams
            self.load_teams()
        else:
            QMessageBox.warning(self, "Connection Failed", "Failed to connect to Linear API. Please check your API key.")
    
    def save_settings(self):
        """Save settings to Linear integration."""
        # Save API key
        api_key = self.api_key_input.text().strip()
        self.linear_integration.set_api_key(api_key)
        
        # Save default team
        team_id = self.team_combo.currentData()
        self.linear_integration.set_default_team(team_id)
        
        # Save default state
        state_id = self.state_combo.currentData()
        self.linear_integration.set_default_state(state_id)
        
        # Save default template
        template_name = self.template_combo.currentData()
        self.linear_integration.set_default_template(template_name)
        
        # Accept dialog
        self.accept()
    
    def apply_dark_theme(self):
        """Apply a dark theme to the dialog elements."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: #e1e1e1;
            }
            QLabel {
                color: #e1e1e1;
                font-weight: bold;
            }
            QGroupBox {
                color: #e1e1e1;
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 4px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }
            QLineEdit, QTextEdit {
                background-color: #383838;
                color: #e1e1e1;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QCheckBox {
                color: #e1e1e1;
            }
            QComboBox {
                background-color: #383838;
                color: #e1e1e1;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox::drop-down {
                border-left: 1px solid #555555;
            }
            QComboBox QAbstractItemView {
                background-color: #383838;
                color: #e1e1e1;
                selection-background-color: #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0086e8;
            }
            QPushButton:pressed {
                background-color: #005fa3;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #aaaaaa;
            }
        """)

class LinearTemplateDialog(QDialog):
    """
    Dialog for selecting a Linear issue template.
    """
    template_selected = pyqtSignal(object)
    
    def __init__(self, linear_integration, parent=None):
        """
        Initialize the Linear template dialog.
        
        Args:
            linear_integration (LinearIntegration): Linear integration instance
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.linear_integration = linear_integration
        
        # Set up the UI
        self.init_ui()
        
        # Load templates
        self.load_templates()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Select Template")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create templates list
        self.templates_list = QListWidget()
        self.templates_list.itemDoubleClicked.connect(self.template_double_clicked)
        main_layout.addWidget(self.templates_list)
        
        # Create buttons
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        
        # Add spacer
        button_layout.addStretch()
        
        # Create Select button
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.select_template)
        button_layout.addWidget(self.select_button)
        
        # Create Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
    
    def load_templates(self):
        """Load templates from Linear integration."""
        # Clear templates list
        self.templates_list.clear()
        
        # Get templates
        templates = self.linear_integration.get_templates()
        
        # Add templates to list
        for template in templates:
            item = QListWidgetItem(template['name'])
            item.setData(Qt.UserRole, template)
            self.templates_list.addItem(item)
        
        # Select default template
        default_template = self.linear_integration.get_default_template()
        if default_template:
            for i in range(self.templates_list.count()):
                item = self.templates_list.item(i)
                template = item.data(Qt.UserRole)
                if template['name'] == default_template['name']:
                    self.templates_list.setCurrentRow(i)
                    break
    
    def select_template(self):
        """Select the current template."""
        row = self.templates_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Template Selected", "Please select a template.")
            return
        
        # Get template
        item = self.templates_list.item(row)
        template = item.data(Qt.UserRole)
        
        # Emit signal
        self.template_selected.emit(template)
        
        # Accept dialog
        self.accept()
    
    def template_double_clicked(self, item):
        """
        Handle template double click.
        
        Args:
            item (QListWidgetItem): Clicked item
        """
        # Get template
        template = item.data(Qt.UserRole)
        
        # Emit signal
        self.template_selected.emit(template)
        
        # Accept dialog
        self.accept()
