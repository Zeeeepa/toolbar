import os
import json
import warnings
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                           QPushButton, QListWidget, QListWidgetItem, QTextEdit, 
                           QTabWidget, QWidget, QFormLayout, QMessageBox, QShortcut, 
                           QInputDialog, QApplication)
from PyQt5.QtGui import QIcon, QKeySequence, QPainter, QColor, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QSize

from Toolbar.core.prompt_templating import PromptTemplate

# Suppress PyQt5 deprecation warnings
warnings.filterwarnings("ignore", message=".*sipPyTypeDict.*")

def create_prompt_icon():
    """Create an icon for the prompt templates button."""
    try:
        # Try to load the SVG icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons", "prompt.svg")
        if os.path.exists(icon_path):
            # Create a QIcon directly from the path
            return QIcon(icon_path)
        
        # If icon file doesn't exist, create a fallback icon
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setPen(QColor(0, 0, 0))
        painter.drawRect(5, 5, 14, 14)
        painter.drawLine(8, 8, 16, 8)
        painter.drawLine(8, 12, 16, 12)
        painter.drawLine(8, 16, 14, 16)
        painter.end()
        return QIcon(pixmap)
    except Exception as e:
        warnings.warn(f"Error creating prompt icon: {e}")
        # Create a very simple fallback icon
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        return QIcon(pixmap)

class PromptTemplatingDialog(QDialog):
    """Dialog for managing prompt templates."""
    
    # Signal emitted when a template is selected for use
    template_selected = pyqtSignal(object)
    
    def __init__(self, template_manager, parent=None):
        """
        Initialize the prompt templating dialog.
        
        Args:
            template_manager (PromptTemplateManager): The template manager
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Prompt Templates")
        self.setMinimumSize(600, 500)
        
        self.template_manager = template_manager
        
        # Set up the UI
        self.init_ui()
        
        # Apply dark theme
        self.apply_dark_theme()
        
        # Load templates
        self.update_template_list()
        
        # Load environment variables
        self.load_env_variables()
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Templates tab
        templates_tab = QWidget()
        templates_layout = QHBoxLayout(templates_tab)
        
        # Left side - template list
        left_layout = QVBoxLayout()
        templates_layout.addLayout(left_layout)
        
        self.template_list = QListWidget()
        self.template_list.currentRowChanged.connect(self.on_template_selected)
        left_layout.addWidget(QLabel("Templates:"))
        left_layout.addWidget(self.template_list)
        
        # Template list buttons
        template_buttons_layout = QHBoxLayout()
        left_layout.addLayout(template_buttons_layout)
        
        self.add_template_button = QPushButton("Add")
        self.add_template_button.clicked.connect(self.add_template)
        template_buttons_layout.addWidget(self.add_template_button)
        
        self.remove_template_button = QPushButton("Remove")
        self.remove_template_button.clicked.connect(self.remove_template)
        template_buttons_layout.addWidget(self.remove_template_button)
        
        # Right side - template editor
        right_layout = QVBoxLayout()
        templates_layout.addLayout(right_layout, 2)  # Give more space to the editor
        
        # Template name
        name_layout = QHBoxLayout()
        right_layout.addLayout(name_layout)
        
        name_layout.addWidget(QLabel("Name:"))
        self.template_name_edit = QLineEdit()
        name_layout.addWidget(self.template_name_edit)
        
        # Shortcut
        name_layout.addWidget(QLabel("Shortcut:"))
        self.shortcut_edit = QLineEdit()
        self.shortcut_edit.setPlaceholderText("Ctrl+Alt+1")
        self.shortcut_edit.setMaximumWidth(100)
        name_layout.addWidget(self.shortcut_edit)
        
        # Template content
        right_layout.addWidget(QLabel("Template:"))
        self.template_content_edit = QTextEdit()
        self.template_content_edit.setPlaceholderText("Enter your prompt template here.\nUse {VariableName} for dynamic variables.")
        right_layout.addWidget(self.template_content_edit)
        
        # Preview section
        right_layout.addWidget(QLabel("Preview:"))
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        right_layout.addWidget(self.preview_text)
        
        # Preview button
        preview_button = QPushButton("Generate Preview")
        preview_button.clicked.connect(self.generate_preview)
        right_layout.addWidget(preview_button)
        
        # Add templates tab
        self.tab_widget.addTab(templates_tab, "Templates")
        
        # Variables tab
        variables_tab = QWidget()
        variables_layout = QVBoxLayout(variables_tab)
        
        # Environment variables form
        self.env_form = QFormLayout()
        variables_layout.addLayout(self.env_form)
        
        # Add variable button
        add_var_button = QPushButton("Add Variable")
        add_var_button.clicked.connect(self.add_variable)
        variables_layout.addWidget(add_var_button)
        
        # Add variables tab
        self.tab_widget.addTab(variables_tab, "Variables")
        
        # Bottom buttons
        buttons_layout = QHBoxLayout()
        main_layout.addLayout(buttons_layout)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_current_template)
        buttons_layout.addWidget(save_button)
        
        use_button = QPushButton("Use Template")
        use_button.clicked.connect(self.use_template)
        buttons_layout.addWidget(use_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        buttons_layout.addWidget(close_button)
    
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
            QListWidget {
                background-color: #383838;
                color: #e1e1e1;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
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
    
    def update_template_list(self):
        """Update the template list widget with current templates."""
        self.template_list.clear()
        
        for template in self.template_manager.get_templates():
            item = QListWidgetItem(template.name)
            item.setData(Qt.UserRole, template)
            self.template_list.addItem(item)
    
    def on_template_selected(self, index):
        """Handle template selection in the list."""
        if index >= 0:
            template = self.template_manager.get_template(index)
            if template:
                # Update the editor fields
                self.template_name_edit.setText(template.name)
                self.template_content_edit.setText(template.content)
                self.shortcut_edit.setText(template.shortcut or "")
                
                # Generate preview
                self.generate_preview()
    
    def add_template(self):
        """Add a new template."""
        # Create a new template with default values
        template = PromptTemplate(name="New Template", content="")
        
        # Add to the templates list
        self.template_manager.add_template(template)
        
        # Update the list widget
        self.update_template_list()
        
        # Select the new template
        self.template_list.setCurrentRow(len(self.template_manager.get_templates()) - 1)
    
    def remove_template(self):
        """Remove the selected template."""
        current_row = self.template_list.currentRow()
        
        if current_row >= 0:
            # Confirm deletion
            confirm = QMessageBox.question(
                self, "Confirm Delete", 
                f"Are you sure you want to delete the template '{self.template_manager.get_template(current_row).name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                # Remove from the templates list
                self.template_manager.remove_template(current_row)
                
                # Update the list widget
                self.update_template_list()
                
                # Clear the editor if no templates left
                if not self.template_manager.get_templates():
                    self.template_name_edit.clear()
                    self.template_content_edit.clear()
                    self.shortcut_edit.clear()
                    self.preview_text.clear()
    
    def save_current_template(self):
        """Save the current template."""
        current_row = self.template_list.currentRow()
        
        if current_row >= 0:
            # Create updated template with values from the editor
            updated_template = PromptTemplate(
                name=self.template_name_edit.text(),
                content=self.template_content_edit.toPlainText(),
                shortcut=self.shortcut_edit.text() or None
            )
            
            # Update the template
            self.template_manager.update_template(current_row, updated_template)
            
            # Update the list widget
            self.update_template_list()
            
            # Select the same template again
            self.template_list.setCurrentRow(current_row)
            
            # Save environment variables
            self.save_env_variables()
            
            QMessageBox.information(self, "Saved", "Template saved successfully.")
    
    def use_template(self):
        """Use the selected template."""
        current_row = self.template_list.currentRow()
        
        if current_row >= 0:
            template = self.template_manager.get_template(current_row)
            if template:
                # Emit the template_selected signal with the selected template
                self.template_selected.emit(template)
                
                # Close the dialog
                self.accept()
    
    def generate_preview(self):
        """Generate a preview of the filled template."""
        current_row = self.template_list.currentRow()
        
        if current_row >= 0:
            # Create a temporary template with the current content
            temp_template = PromptTemplate(
                name=self.template_name_edit.text(),
                content=self.template_content_edit.toPlainText()
            )
            
            # Get variables from form
            variables = {}
            for i in range(self.env_form.rowCount()):
                label_item = self.env_form.itemAt(i, QFormLayout.LabelRole)
                field_item = self.env_form.itemAt(i, QFormLayout.FieldRole)
                
                if label_item and field_item:
                    var_name = label_item.widget().text().strip(":")
                    var_value = field_item.widget().text()
                    variables[var_name] = var_value
            
            # Fill the template and show in the preview
            filled_content = temp_template.fill_template(variables)
            self.preview_text.setText(filled_content)
    
    def load_env_variables(self):
        """Load environment variables and create form fields."""
        # Clear existing form fields
        while self.env_form.rowCount() > 0:
            self.env_form.removeRow(0)
        
        # Get all variables used in templates
        all_variables = set()
        for template in self.template_manager.get_templates():
            all_variables.update(template.get_variables())
        
        # Add form fields for each variable
        for var in sorted(all_variables):
            line_edit = QLineEdit()
            line_edit.setText(os.environ.get(var, ""))
            self.env_form.addRow(f"{var}:", line_edit)
    
    def save_env_variables(self):
        """Save environment variables to .env file."""
        dotenv_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        
        # Create .env file if it doesn't exist
        if not os.path.exists(dotenv_file):
            with open(dotenv_file, 'w') as f:
                pass
        
        # Read existing .env file
        env_vars = {}
        if os.path.exists(dotenv_file):
            with open(dotenv_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip().strip('"\'')
        
        # Update with new values
        for i in range(self.env_form.rowCount()):
            label_item = self.env_form.itemAt(i, QFormLayout.LabelRole)
            field_item = self.env_form.itemAt(i, QFormLayout.FieldRole)
            
            if label_item and field_item:
                var_name = label_item.widget().text().strip(":")
                var_value = field_item.widget().text()
                env_vars[var_name] = var_value
        
        # Write back to .env file
        with open(dotenv_file, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
    
    def add_variable(self):
        """Add a new environment variable."""
        var_name, ok = QInputDialog.getText(
            self, "Add Variable", "Enter variable name:"
        )
        
        if ok and var_name:
            # Check if variable already exists
            for i in range(self.env_form.rowCount()):
                label_item = self.env_form.itemAt(i, QFormLayout.LabelRole)
                if label_item and label_item.widget().text().strip(":") == var_name:
                    QMessageBox.warning(self, "Error", f"Variable '{var_name}' already exists.")
                    return
            
            # Add new variable to form
            line_edit = QLineEdit()
            self.env_form.addRow(f"{var_name}:", line_edit)
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Ask to save changes
        if self.template_list.currentRow() >= 0:
            reply = QMessageBox.question(
                self, "Save Changes", 
                "Do you want to save changes before closing?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                self.save_current_template()
                event.accept()
            elif reply == QMessageBox.Cancel:
                event.ignore()
            else:
                event.accept()
        else:
            event.accept()
