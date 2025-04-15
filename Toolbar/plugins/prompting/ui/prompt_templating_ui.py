"""
UI for the prompting plugin.
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, 
    QListWidgetItem, QSplitter, QTextEdit, QDialog, QLineEdit, QFormLayout,
    QDialogButtonBox, QMessageBox, QMenu, QAction, QToolBar, QMainWindow,
    QDockWidget, QTabWidget, QComboBox, QCheckBox, QGroupBox, QScrollArea,
    QFileDialog, QInputDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QSyntaxHighlighter, QTextCharFormat, QColor

logger = logging.getLogger(__name__)

class TemplateEditorDialog(QDialog):
    """Dialog for editing prompt templates."""
    
    def __init__(self, template=None, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        self.template = template or {
            "id": "",
            "name": "",
            "description": "",
            "template": "",
            "variables": [],
            "author": "",
            "version": "1.0.0",
            "tags": [],
            "model": ""
        }
        
        self.setWindowTitle("Template Editor")
        self.setMinimumSize(800, 600)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create form layout for metadata
        form_layout = QFormLayout()
        layout.addLayout(form_layout)
        
        # Add ID field
        self.id_edit = QLineEdit(self.template["id"])
        form_layout.addRow("ID:", self.id_edit)
        
        # Add name field
        self.name_edit = QLineEdit(self.template["name"])
        form_layout.addRow("Name:", self.name_edit)
        
        # Add description field
        self.description_edit = QLineEdit(self.template["description"])
        form_layout.addRow("Description:", self.description_edit)
        
        # Add author field
        self.author_edit = QLineEdit(self.template["author"])
        form_layout.addRow("Author:", self.author_edit)
        
        # Add version field
        self.version_edit = QLineEdit(self.template["version"])
        form_layout.addRow("Version:", self.version_edit)
        
        # Add tags field
        self.tags_edit = QLineEdit(", ".join(self.template["tags"]))
        form_layout.addRow("Tags:", self.tags_edit)
        
        # Add model field
        self.model_edit = QLineEdit(self.template.get("model", ""))
        form_layout.addRow("Model:", self.model_edit)
        
        # Add template editor
        layout.addWidget(QLabel("Template:"))
        self.template_edit = QTextEdit()
        self.template_edit.setFont(QFont("Courier New", 10))
        self.template_edit.setPlainText(self.template["template"])
        self.template_edit.textChanged.connect(self._extract_variables)
        layout.addWidget(self.template_edit)
        
        # Add variables section
        layout.addWidget(QLabel("Variables:"))
        
        # Create variables table
        self.variables_table = QTableWidget(0, 3)
        self.variables_table.setHorizontalHeaderLabels(["Name", "Description", "Default Value"])
        self.variables_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.variables_table)
        
        # Add variable buttons
        var_buttons_layout = QHBoxLayout()
        layout.addLayout(var_buttons_layout)
        
        # Add add variable button
        add_var_button = QPushButton("Add Variable")
        add_var_button.clicked.connect(self._add_variable)
        var_buttons_layout.addWidget(add_var_button)
        
        # Add remove variable button
        remove_var_button = QPushButton("Remove Variable")
        remove_var_button.clicked.connect(self._remove_variable)
        var_buttons_layout.addWidget(remove_var_button)
        
        # Initialize variables table
        self._init_variables_table()
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _init_variables_table(self):
        """Initialize the variables table."""
        # Clear the table
        self.variables_table.setRowCount(0)
        
        # Add existing variables
        for var in self.template["variables"]:
            self._add_variable_row(var)
    
    def _add_variable_row(self, var=None):
        """Add a row to the variables table."""
        var = var or {"name": "", "description": "", "default": ""}
        
        # Add a new row
        row = self.variables_table.rowCount()
        self.variables_table.insertRow(row)
        
        # Add name cell
        name_item = QTableWidgetItem(var.get("name", ""))
        self.variables_table.setItem(row, 0, name_item)
        
        # Add description cell
        desc_item = QTableWidgetItem(var.get("description", ""))
        self.variables_table.setItem(row, 1, desc_item)
        
        # Add default value cell
        default_item = QTableWidgetItem(str(var.get("default", "")))
        self.variables_table.setItem(row, 2, default_item)
    
    def _add_variable(self):
        """Add a new variable."""
        self._add_variable_row()
    
    def _remove_variable(self):
        """Remove the selected variable."""
        selected_rows = self.variables_table.selectedIndexes()
        if not selected_rows:
            return
        
        # Get the row to remove
        row = selected_rows[0].row()
        
        # Remove the row
        self.variables_table.removeRow(row)
    
    def _extract_variables(self):
        """Extract variables from the template."""
        try:
            # Get the template text
            template_text = self.template_edit.toPlainText()
            
            # Extract variable names
            import re
            pattern = r"\{([a-zA-Z0-9_]+)\}"
            matches = re.findall(pattern, template_text)
            
            # Get unique variable names
            var_names = list(set(matches))
            
            # Get existing variables
            existing_vars = {}
            for row in range(self.variables_table.rowCount()):
                name_item = self.variables_table.item(row, 0)
                if name_item and name_item.text():
                    existing_vars[name_item.text()] = row
            
            # Add new variables
            for var_name in var_names:
                if var_name not in existing_vars:
                    self._add_variable_row({"name": var_name, "description": "", "default": ""})
        except Exception as e:
            logger.error(f"Error extracting variables: {e}", exc_info=True)
    
    def get_template(self):
        """Get the edited template."""
        # Get variables from table
        variables = []
        for row in range(self.variables_table.rowCount()):
            name_item = self.variables_table.item(row, 0)
            desc_item = self.variables_table.item(row, 1)
            default_item = self.variables_table.item(row, 2)
            
            if name_item and name_item.text():
                variables.append({
                    "name": name_item.text(),
                    "description": desc_item.text() if desc_item else "",
                    "default": default_item.text() if default_item else ""
                })
        
        return {
            "id": self.id_edit.text(),
            "name": self.name_edit.text(),
            "description": self.description_edit.text(),
            "template": self.template_edit.toPlainText(),
            "variables": variables,
            "author": self.author_edit.text(),
            "version": self.version_edit.text(),
            "tags": [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()],
            "model": self.model_edit.text()
        }

class TemplateRenderDialog(QDialog):
    """Dialog for rendering a prompt template."""
    
    def __init__(self, template, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        self.template = template
        
        self.setWindowTitle(f"Render Template: {template['name']}")
        self.setMinimumSize(600, 400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add template info
        info_text = f"""
            <h2>{template['name']}</h2>
            <p>{template['description']}</p>
        """
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Add variables section
        layout.addWidget(QLabel("Variables:"))
        
        # Create form layout for variables
        form_layout = QFormLayout()
        layout.addLayout(form_layout)
        
        # Add variable fields
        self.var_fields = {}
        for var in template["variables"]:
            var_name = var["name"]
            var_desc = var["description"]
            var_default = var["default"]
            
            # Create field
            field = QLineEdit(var_default)
            
            # Add tooltip with description
            if var_desc:
                field.setToolTip(var_desc)
            
            # Add to form
            form_layout.addRow(f"{var_name}:", field)
            
            # Store field
            self.var_fields[var_name] = field
        
        # Add preview button
        preview_button = QPushButton("Preview")
        preview_button.clicked.connect(self._preview_template)
        layout.addWidget(preview_button)
        
        # Add preview area
        layout.addWidget(QLabel("Preview:"))
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Initial preview
        self._preview_template()
    
    def _preview_template(self):
        """Preview the rendered template."""
        try:
            # Get variable values
            variables = {}
            for var_name, field in self.var_fields.items():
                variables[var_name] = field.text()
            
            # Render template
            template_text = self.template["template"]
            result = template_text
            
            # Replace variables in the template
            for var_name, var_value in variables.items():
                placeholder = f"{{{var_name}}}"
                result = result.replace(placeholder, var_value)
            
            # Update preview
            self.preview_text.setPlainText(result)
        except Exception as e:
            logger.error(f"Error previewing template: {e}", exc_info=True)
            self.preview_text.setPlainText(f"Error: {str(e)}")
    
    def get_variables(self):
        """Get the variable values."""
        variables = {}
        for var_name, field in self.var_fields.items():
            variables[var_name] = field.text()
        return variables

class PromptTemplatingUI(QMainWindow):
    """UI for the prompting plugin."""
    
    def __init__(self, plugin, parent=None):
        """Initialize the UI."""
        super().__init__(parent)
        self.plugin = plugin
        
        self.setWindowTitle("Prompt Templates")
        self.setMinimumSize(800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Add new template action
        new_action = QAction(QIcon.fromTheme("document-new"), "New Template", self)
        new_action.triggered.connect(self.new_template)
        toolbar.addAction(new_action)
        
        # Add edit template action
        edit_action = QAction(QIcon.fromTheme("document-edit"), "Edit Template", self)
        edit_action.triggered.connect(self.edit_template)
        toolbar.addAction(edit_action)
        
        # Add delete template action
        delete_action = QAction(QIcon.fromTheme("edit-delete"), "Delete Template", self)
        delete_action.triggered.connect(self.delete_template)
        toolbar.addAction(delete_action)
        
        # Add render template action
        render_action = QAction(QIcon.fromTheme("document-send"), "Render Template", self)
        render_action.triggered.connect(self.render_template)
        toolbar.addAction(render_action)
        
        # Add separator
        toolbar.addSeparator()
        
        # Add refresh action
        refresh_action = QAction(QIcon.fromTheme("view-refresh"), "Refresh", self)
        refresh_action.triggered.connect(self.refresh_templates)
        toolbar.addAction(refresh_action)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create template list
        self.template_list = QListWidget()
        self.template_list.setMinimumWidth(200)
        self.template_list.currentItemChanged.connect(self.template_selected)
        splitter.addWidget(self.template_list)
        
        # Create template details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Add template details
        self.details_label = QLabel()
        details_layout.addWidget(self.details_label)
        
        # Add template content
        self.template_view = QTextEdit()
        self.template_view.setReadOnly(True)
        self.template_view.setFont(QFont("Courier New", 10))
        details_layout.addWidget(self.template_view)
        
        # Add variables section
        details_layout.addWidget(QLabel("Variables:"))
        self.variables_table = QTableWidget(0, 3)
        self.variables_table.setHorizontalHeaderLabels(["Name", "Description", "Default Value"])
        self.variables_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        details_layout.addWidget(self.variables_table)
        
        splitter.addWidget(details_widget)
        
        # Set splitter sizes
        splitter.setSizes([200, 600])
        
        # Load templates
        self.refresh_templates()
    
    def refresh_templates(self):
        """Refresh the template list."""
        try:
            # Clear the list
            self.template_list.clear()
            
            # Get templates from plugin
            templates = self.plugin.get_templates()
            
            # Add templates to list
            for template in templates:
                item = QListWidgetItem(template["name"])
                item.setData(Qt.UserRole, template)
                self.template_list.addItem(item)
            
            # Select the first template
            if self.template_list.count() > 0:
                self.template_list.setCurrentRow(0)
            else:
                self.details_label.setText("No templates available")
                self.template_view.clear()
                self.variables_table.setRowCount(0)
        except Exception as e:
            logger.error(f"Error refreshing templates: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error refreshing templates: {str(e)}")
    
    def template_selected(self, current, previous):
        """Handle template selection."""
        if not current:
            self.details_label.setText("No template selected")
            self.template_view.clear()
            self.variables_table.setRowCount(0)
            return
        
        try:
            # Get template data
            template = current.data(Qt.UserRole)
            
            # Update details
            self.details_label.setText(f"""
                <h2>{template["name"]}</h2>
                <p><b>ID:</b> {template["id"]}</p>
                <p><b>Description:</b> {template["description"]}</p>
                <p><b>Author:</b> {template["author"]}</p>
                <p><b>Version:</b> {template["version"]}</p>
                <p><b>Tags:</b> {", ".join(template["tags"])}</p>
                <p><b>Model:</b> {template.get("model", "")}</p>
            """)
            
            # Update template view
            self.template_view.setPlainText(template["template"])
            
            # Update variables table
            self.variables_table.setRowCount(0)
            for var in template["variables"]:
                row = self.variables_table.rowCount()
                self.variables_table.insertRow(row)
                
                # Add name cell
                name_item = QTableWidgetItem(var.get("name", ""))
                self.variables_table.setItem(row, 0, name_item)
                
                # Add description cell
                desc_item = QTableWidgetItem(var.get("description", ""))
                self.variables_table.setItem(row, 1, desc_item)
                
                # Add default value cell
                default_item = QTableWidgetItem(str(var.get("default", "")))
                self.variables_table.setItem(row, 2, default_item)
        except Exception as e:
            logger.error(f"Error displaying template: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error displaying template: {str(e)}")
    
    def new_template(self):
        """Create a new template."""
        try:
            # Show template editor dialog
            dialog = TemplateEditorDialog(parent=self)
            if dialog.exec_() == QDialog.Accepted:
                # Get template data
                template = dialog.get_template()
                
                # Validate template
                if not template["id"]:
                    QMessageBox.warning(self, "Validation Error", "Template ID is required")
                    return
                
                if not template["name"]:
                    QMessageBox.warning(self, "Validation Error", "Template name is required")
                    return
                
                # Create template
                if self.plugin.create_template(template):
                    QMessageBox.information(self, "Success", f"Template {template['name']} created successfully")
                    self.refresh_templates()
                else:
                    QMessageBox.critical(self, "Error", f"Failed to create template {template['name']}")
        except Exception as e:
            logger.error(f"Error creating template: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error creating template: {str(e)}")
    
    def edit_template(self):
        """Edit the selected template."""
        try:
            # Get selected template
            current_item = self.template_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select a template to edit")
                return
            
            # Get template data
            template = current_item.data(Qt.UserRole)
            
            # Show template editor dialog
            dialog = TemplateEditorDialog(template, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                # Get edited template data
                edited_template = dialog.get_template()
                
                # Validate template
                if not edited_template["id"]:
                    QMessageBox.warning(self, "Validation Error", "Template ID is required")
                    return
                
                if not edited_template["name"]:
                    QMessageBox.warning(self, "Validation Error", "Template name is required")
                    return
                
                # Update template
                if self.plugin.update_template(template["id"], edited_template):
                    QMessageBox.information(self, "Success", f"Template {edited_template['name']} updated successfully")
                    self.refresh_templates()
                else:
                    QMessageBox.critical(self, "Error", f"Failed to update template {edited_template['name']}")
        except Exception as e:
            logger.error(f"Error editing template: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error editing template: {str(e)}")
    
    def delete_template(self):
        """Delete the selected template."""
        try:
            # Get selected template
            current_item = self.template_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select a template to delete")
                return
            
            # Get template data
            template = current_item.data(Qt.UserRole)
            
            # Confirm deletion
            if QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete template {template['name']}?",
                QMessageBox.Yes | QMessageBox.No
            ) != QMessageBox.Yes:
                return
            
            # Delete template
            if self.plugin.delete_template(template["id"]):
                QMessageBox.information(self, "Success", f"Template {template['name']} deleted successfully")
                self.refresh_templates()
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete template {template['name']}")
        except Exception as e:
            logger.error(f"Error deleting template: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error deleting template: {str(e)}")
    
    def render_template(self):
        """Render the selected template."""
        try:
            # Get selected template
            current_item = self.template_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select a template to render")
                return
            
            # Get template data
            template = current_item.data(Qt.UserRole)
            
            # Show render dialog
            dialog = TemplateRenderDialog(template, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                # Get variable values
                variables = dialog.get_variables()
                
                # Render template
                result = self.plugin.render_template(template["id"], variables)
                
                # Show result
                result_dialog = QDialog(self)
                result_dialog.setWindowTitle("Rendered Template")
                result_dialog.setMinimumSize(600, 400)
                
                # Create layout
                layout = QVBoxLayout(result_dialog)
                
                # Add result text
                result_text = QTextEdit()
                result_text.setPlainText(result)
                result_text.setReadOnly(True)
                layout.addWidget(result_text)
                
                # Add copy button
                copy_button = QPushButton("Copy to Clipboard")
                copy_button.clicked.connect(lambda: self._copy_to_clipboard(result))
                layout.addWidget(copy_button)
                
                # Add close button
                close_button = QPushButton("Close")
                close_button.clicked.connect(result_dialog.accept)
                layout.addWidget(close_button)
                
                # Show dialog
                result_dialog.exec_()
        except Exception as e:
            logger.error(f"Error rendering template: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error rendering template: {str(e)}")
    
    def _copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        try:
            from PyQt5.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "Success", "Text copied to clipboard")
        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error copying to clipboard: {str(e)}")
    
    def cleanup(self):
        """Clean up resources."""
        pass
