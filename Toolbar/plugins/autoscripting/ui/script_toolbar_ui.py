"""
UI for the autoscripting plugin.
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
    QFileDialog, QInputDialog
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QSyntaxHighlighter, QTextCharFormat, QColor

logger = logging.getLogger(__name__)

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Python code."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#569CD6"))
        self.keyword_format.setFontWeight(QFont.Bold)
        
        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor("#DCDCAA"))
        
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))
        
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6A9955"))
        
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#B5CEA8"))
        
        # Python keywords
        self.keywords = [
            "and", "as", "assert", "break", "class", "continue", "def",
            "del", "elif", "else", "except", "False", "finally", "for",
            "from", "global", "if", "import", "in", "is", "lambda", "None",
            "nonlocal", "not", "or", "pass", "raise", "return", "True",
            "try", "while", "with", "yield"
        ]
    
    def highlightBlock(self, text):
        """Highlight a block of text."""
        # Keywords
        for word in text.split():
            if word in self.keywords:
                index = text.find(word)
                while index >= 0:
                    # Check if it's a whole word
                    if (index == 0 or not text[index-1].isalnum()) and \
                       (index + len(word) == len(text) or not text[index + len(word)].isalnum()):
                        self.setFormat(index, len(word), self.keyword_format)
                    index = text.find(word, index + 1)
        
        # Strings (simple implementation)
        in_string = False
        quote_char = None
        for i, char in enumerate(text):
            if char in ["'", "\""]:
                if not in_string:
                    in_string = True
                    quote_char = char
                    start = i
                elif char == quote_char:
                    in_string = False
                    self.setFormat(start, i - start + 1, self.string_format)
        
        # Comments
        comment_pos = text.find("#")
        if comment_pos >= 0:
            self.setFormat(comment_pos, len(text) - comment_pos, self.comment_format)
        
        # Numbers (simple implementation)
        for word in text.split():
            try:
                float(word)
                index = text.find(word)
                while index >= 0:
                    # Check if it's a whole word
                    if (index == 0 or not text[index-1].isalnum()) and \
                       (index + len(word) == len(text) or not text[index + len(word)].isalnum()):
                        self.setFormat(index, len(word), self.number_format)
                    index = text.find(word, index + 1)
            except ValueError:
                pass

class ScriptEditorDialog(QDialog):
    """Dialog for editing scripts."""
    
    def __init__(self, script=None, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        self.script = script or {
            "id": "",
            "name": "",
            "description": "",
            "code": "",
            "author": "",
            "version": "1.0.0",
            "tags": []
        }
        
        self.setWindowTitle("Script Editor")
        self.setMinimumSize(800, 600)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create form layout for metadata
        form_layout = QFormLayout()
        layout.addLayout(form_layout)
        
        # Add ID field
        self.id_edit = QLineEdit(self.script["id"])
        form_layout.addRow("ID:", self.id_edit)
        
        # Add name field
        self.name_edit = QLineEdit(self.script["name"])
        form_layout.addRow("Name:", self.name_edit)
        
        # Add description field
        self.description_edit = QLineEdit(self.script["description"])
        form_layout.addRow("Description:", self.description_edit)
        
        # Add author field
        self.author_edit = QLineEdit(self.script["author"])
        form_layout.addRow("Author:", self.author_edit)
        
        # Add version field
        self.version_edit = QLineEdit(self.script["version"])
        form_layout.addRow("Version:", self.version_edit)
        
        # Add tags field
        self.tags_edit = QLineEdit(", ".join(self.script["tags"]))
        form_layout.addRow("Tags:", self.tags_edit)
        
        # Add code editor
        layout.addWidget(QLabel("Code:"))
        self.code_edit = QTextEdit()
        self.code_edit.setFont(QFont("Courier New", 10))
        self.code_edit.setPlainText(self.script["code"])
        
        # Add syntax highlighting
        self.highlighter = PythonSyntaxHighlighter(self.code_edit.document())
        
        layout.addWidget(self.code_edit)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_script(self):
        """Get the edited script."""
        return {
            "id": self.id_edit.text(),
            "name": self.name_edit.text(),
            "description": self.description_edit.text(),
            "code": self.code_edit.toPlainText(),
            "author": self.author_edit.text(),
            "version": self.version_edit.text(),
            "tags": [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]
        }

class ScriptToolbarUI(QMainWindow):
    """UI for the autoscripting plugin."""
    
    def __init__(self, plugin, parent=None):
        """Initialize the UI."""
        super().__init__(parent)
        self.plugin = plugin
        
        self.setWindowTitle("Script Manager")
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
        
        # Add new script action
        new_action = QAction(QIcon.fromTheme("document-new"), "New Script", self)
        new_action.triggered.connect(self.new_script)
        toolbar.addAction(new_action)
        
        # Add edit script action
        edit_action = QAction(QIcon.fromTheme("document-edit"), "Edit Script", self)
        edit_action.triggered.connect(self.edit_script)
        toolbar.addAction(edit_action)
        
        # Add delete script action
        delete_action = QAction(QIcon.fromTheme("edit-delete"), "Delete Script", self)
        delete_action.triggered.connect(self.delete_script)
        toolbar.addAction(delete_action)
        
        # Add run script action
        run_action = QAction(QIcon.fromTheme("media-playback-start"), "Run Script", self)
        run_action.triggered.connect(self.run_script)
        toolbar.addAction(run_action)
        
        # Add separator
        toolbar.addSeparator()
        
        # Add refresh action
        refresh_action = QAction(QIcon.fromTheme("view-refresh"), "Refresh", self)
        refresh_action.triggered.connect(self.refresh_scripts)
        toolbar.addAction(refresh_action)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create script list
        self.script_list = QListWidget()
        self.script_list.setMinimumWidth(200)
        self.script_list.currentItemChanged.connect(self.script_selected)
        splitter.addWidget(self.script_list)
        
        # Create script details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Add script details
        self.details_label = QLabel()
        details_layout.addWidget(self.details_label)
        
        # Add script code
        self.code_view = QTextEdit()
        self.code_view.setReadOnly(True)
        self.code_view.setFont(QFont("Courier New", 10))
        
        # Add syntax highlighting
        self.highlighter = PythonSyntaxHighlighter(self.code_view.document())
        
        details_layout.addWidget(self.code_view)
        
        splitter.addWidget(details_widget)
        
        # Set splitter sizes
        splitter.setSizes([200, 600])
        
        # Load scripts
        self.refresh_scripts()
    
    def refresh_scripts(self):
        """Refresh the script list."""
        try:
            # Clear the list
            self.script_list.clear()
            
            # Get scripts from plugin
            scripts = self.plugin.get_scripts()
            
            # Add scripts to list
            for script in scripts:
                item = QListWidgetItem(script["name"])
                item.setData(Qt.UserRole, script)
                self.script_list.addItem(item)
            
            # Select the first script
            if self.script_list.count() > 0:
                self.script_list.setCurrentRow(0)
            else:
                self.details_label.setText("No scripts available")
                self.code_view.clear()
        except Exception as e:
            logger.error(f"Error refreshing scripts: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error refreshing scripts: {str(e)}")
    
    def script_selected(self, current, previous):
        """Handle script selection."""
        if not current:
            self.details_label.setText("No script selected")
            self.code_view.clear()
            return
        
        try:
            # Get script data
            script = current.data(Qt.UserRole)
            
            # Update details
            self.details_label.setText(f"""
                <h2>{script["name"]}</h2>
                <p><b>ID:</b> {script["id"]}</p>
                <p><b>Description:</b> {script["description"]}</p>
                <p><b>Author:</b> {script["author"]}</p>
                <p><b>Version:</b> {script["version"]}</p>
                <p><b>Tags:</b> {", ".join(script["tags"])}</p>
            """)
            
            # Update code view
            self.code_view.setPlainText(script["code"])
        except Exception as e:
            logger.error(f"Error displaying script: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error displaying script: {str(e)}")
    
    def new_script(self):
        """Create a new script."""
        try:
            # Show script editor dialog
            dialog = ScriptEditorDialog(parent=self)
            if dialog.exec_() == QDialog.Accepted:
                # Get script data
                script = dialog.get_script()
                
                # Validate script
                if not script["id"]:
                    QMessageBox.warning(self, "Validation Error", "Script ID is required")
                    return
                
                if not script["name"]:
                    QMessageBox.warning(self, "Validation Error", "Script name is required")
                    return
                
                # Create script
                if self.plugin.create_script(script):
                    QMessageBox.information(self, "Success", f"Script {script['name']} created successfully")
                    self.refresh_scripts()
                else:
                    QMessageBox.critical(self, "Error", f"Failed to create script {script['name']}")
        except Exception as e:
            logger.error(f"Error creating script: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error creating script: {str(e)}")
    
    def edit_script(self):
        """Edit the selected script."""
        try:
            # Get selected script
            current_item = self.script_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select a script to edit")
                return
            
            # Get script data
            script = current_item.data(Qt.UserRole)
            
            # Show script editor dialog
            dialog = ScriptEditorDialog(script, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                # Get edited script data
                edited_script = dialog.get_script()
                
                # Validate script
                if not edited_script["id"]:
                    QMessageBox.warning(self, "Validation Error", "Script ID is required")
                    return
                
                if not edited_script["name"]:
                    QMessageBox.warning(self, "Validation Error", "Script name is required")
                    return
                
                # Update script
                if self.plugin.update_script(script["id"], edited_script):
                    QMessageBox.information(self, "Success", f"Script {edited_script['name']} updated successfully")
                    self.refresh_scripts()
                else:
                    QMessageBox.critical(self, "Error", f"Failed to update script {edited_script['name']}")
        except Exception as e:
            logger.error(f"Error editing script: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error editing script: {str(e)}")
    
    def delete_script(self):
        """Delete the selected script."""
        try:
            # Get selected script
            current_item = self.script_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select a script to delete")
                return
            
            # Get script data
            script = current_item.data(Qt.UserRole)
            
            # Confirm deletion
            if QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete script {script['name']}?",
                QMessageBox.Yes | QMessageBox.No
            ) != QMessageBox.Yes:
                return
            
            # Delete script
            if self.plugin.delete_script(script["id"]):
                QMessageBox.information(self, "Success", f"Script {script['name']} deleted successfully")
                self.refresh_scripts()
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete script {script['name']}")
        except Exception as e:
            logger.error(f"Error deleting script: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error deleting script: {str(e)}")
    
    def run_script(self):
        """Run the selected script."""
        try:
            # Get selected script
            current_item = self.script_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select a script to run")
                return
            
            # Get script data
            script = current_item.data(Qt.UserRole)
            
            # Run script
            result = self.plugin.run_script(script["id"])
            
            # Show result
            QMessageBox.information(
                self,
                "Script Result",
                f"Script {script['name']} executed successfully.\n\nResult: {result}"
            )
        except Exception as e:
            logger.error(f"Error running script: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error running script: {str(e)}")
    
    def cleanup(self):
        """Clean up resources."""
        pass
