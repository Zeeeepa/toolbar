import os
import sys
import warnings
import re
import logging
from PyQt5.QtWidgets import (QMainWindow, QToolBar, QAction, QFileDialog, 
                            QInputDialog, QMenu, QMessageBox, QLabel, QWidget, 
                            QHBoxLayout, QVBoxLayout, QShortcut, QDesktopWidget,
                            QToolButton, QApplication, QSizePolicy, QPushButton)
from PyQt5.QtGui import QIcon, QCursor, QKeySequence, QColor, QPalette
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer

from Toolbar.core.script_manager import ScriptManager
from Toolbar.core.prompt_templating import PromptTemplateManager
from Toolbar.ui.prompt_templating_ui import PromptTemplatingDialog
from Toolbar.ui.toolbar_settings import ToolbarSettingsDialog
from Toolbar.ui.github_settings import GitHubSettingsDialog
from Toolbar.ui.linear_settings import LinearSettingsDialog
from Toolbar.ui.github_project_ui import GitHubProjectsDialog
from Toolbar.ui.github_ui import GitHubUI

class ScriptToolbar(QMainWindow):
    """Main toolbar window for script execution."""
    
    def __init__(self, config, plugin_manager, parent=None):
        """
        Initialize the toolbar.
        
        Args:
            config: Configuration object
            plugin_manager: Plugin manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config
        self.plugin_manager = plugin_manager
        
        # Get plugin instances
        self.github_plugin = plugin_manager.get_plugin("GitHub Integration")
        self.linear_plugin = plugin_manager.get_plugin("Linear Integration")
        
        # Initialize UI
        self.init_ui()
        
        # Apply settings
        self.apply_settings()
    
    def init_ui(self):
        """Initialize the toolbar UI."""
        try:
            # Set window title and flags
            self.setWindowTitle("Script Toolbar")
            
            # Reset window flags to ensure proper positioning
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
            
            # Allow some transparency but not too much
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            
            # Create central widget and layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Main layout
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # Create toolbar widget
            toolbar_widget = QWidget()
            toolbar_widget.setObjectName("toolbarWidget")
            self.toolbar_layout = QHBoxLayout(toolbar_widget)
            self.toolbar_layout.setContentsMargins(5, 5, 5, 5)
            self.toolbar_layout.setSpacing(5)
            
            # Set context menu policy for the toolbar
            toolbar_widget.setContextMenuPolicy(Qt.CustomContextMenu)
            toolbar_widget.customContextMenuRequested.connect(self.show_toolbar_context_menu)
            
            # Add toolbar to main layout
            main_layout.addWidget(toolbar_widget)
            
            # Styles - use a more visible background color
            self.setStyleSheet("""
                QWidget#toolbarWidget {
                    background-color: #333333;
                    border: 1px solid #555555;
                    border-radius: 5px;
                }
                QPushButton {
                    border: none;
                    border-radius: 4px;
                    background-color: transparent;
                    color: white;
                    font-weight: bold;
                    padding: 5px;
                    min-height: 30px;
                }
                QPushButton:hover {
                    background-color: rgba(100, 100, 100, 150);
                }
                QLabel {
                    color: white;
                    font-weight: bold;
                }
            """)
            
            # Set initial width to full screen width
            desktop = QDesktopWidget().availableGeometry()
            self.setFixedWidth(desktop.width())
            self.setFixedHeight(40)  # Fixed height instead of minimum
            
            # Position at the very top of the screen
            self.move(0, 0)
            
            # Add script buttons
            for script in self.config.get_scripts():
                self.add_script_button(script)
            
            # Get center_images setting (safely)
            center_images = False
            try:
                # First try direct dictionary access
                center_images = self.config.config.get('ui', {}).get('center_images', False)
            except Exception as e:
                warnings.warn(f"Failed to access config.config directly: {e}")
                try:
                    # Fall back to get method
                    center_images = self.config.get('ui', 'center_images', False)
                except Exception as e2:
                    warnings.warn(f"Failed to get center_images setting: {e2}")
            
            # Add spacer if center_images is enabled
            if center_images:
                spacer = QWidget()
                spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                self.toolbar_layout.addWidget(spacer)
            
            # Add prompt templates button
            prompt_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                         "icons", "prompt.svg")
            if os.path.exists(prompt_icon_path):
                prompt_button = QPushButton()
                prompt_button.setIcon(QIcon(prompt_icon_path))
                prompt_button.setIconSize(QSize(24, 24))
                prompt_button.setToolTip("Prompt Templates")
                prompt_button.clicked.connect(self.show_prompt_templates)
                self.toolbar_layout.addWidget(prompt_button)
                self.prompt_button = prompt_button
            
            # Add settings button
            settings_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                           "icons", "settings.svg")
            if os.path.exists(settings_icon_path):
                settings_button = QPushButton()
                settings_button.setIcon(QIcon(settings_icon_path))
                settings_button.setIconSize(QSize(24, 24))
                settings_button.setToolTip("Settings")
                settings_button.clicked.connect(self.show_toolbar_settings)
                self.toolbar_layout.addWidget(settings_button)
            
            # Add GitHub button (always show it, even if github_monitor is None)
            github_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                        "icons", "github.svg")
            if os.path.exists(github_icon_path):
                github_button = QPushButton()
                github_button.setIcon(QIcon(github_icon_path))
                github_button.setIconSize(QSize(24, 24))
                github_button.setToolTip("GitHub Settings")
                github_button.clicked.connect(self.show_github_settings)
                self.toolbar_layout.addWidget(github_button)
                self.github_button = github_button
            
            # Add Linear settings button if Linear integration is available
            if self.linear_plugin:
                linear_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                              "icons", "linear.svg")
                if os.path.exists(linear_icon_path):
                    linear_button = QPushButton()
                    linear_button.setIcon(QIcon(linear_icon_path))
                    linear_button.setIconSize(QSize(24, 24))
                    linear_button.setToolTip("Linear Settings")
                    linear_button.clicked.connect(self.show_linear_settings)
                    self.toolbar_layout.addWidget(linear_button)
                    self.linear_button = linear_button
            
            # Add another spacer if center_images is enabled
            if center_images:
                spacer2 = QWidget()
                spacer2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                self.toolbar_layout.addWidget(spacer2)
            
            # Add "Add Script" button
            add_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                       "icons", "add.svg")
            if os.path.exists(add_icon_path):
                add_button = QPushButton()
                add_button.setIcon(QIcon(add_icon_path))
                add_button.setIconSize(QSize(24, 24))
                add_button.setToolTip("Add Script")
                add_button.clicked.connect(self.add_script)
                self.toolbar_layout.addWidget(add_button)
            
            # Add exit button
            exit_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                        "icons", "exit.svg")
            if os.path.exists(exit_icon_path):
                exit_button = QPushButton()
                exit_button.setIcon(QIcon(exit_icon_path))
                exit_button.setIconSize(QSize(24, 24))
                exit_button.setToolTip("Exit")
                exit_button.clicked.connect(self.close)
                self.toolbar_layout.addWidget(exit_button)
            else:
                # Use text if icon doesn't exist
                exit_button = QPushButton()
                exit_button.setText("Exit")
                exit_button.setToolTip("Exit")
                exit_button.clicked.connect(self.close)
                self.toolbar_layout.addWidget(exit_button)
            
            # Add default prompts
            self.add_default_prompts()
            
            # Set up keyboard shortcuts
            self.setup_prompt_shortcuts()
            
            # Apply settings
            self.apply_settings()
        except Exception as e:
            warnings.warn(f"Failed to initialize UI: {e}")
    
    def calculate_toolbar_width(self):
        """Calculate the width of the toolbar based on screen size."""
        desktop = QDesktopWidget().availableGeometry()
        return desktop.width()
    
    def position_toolbar(self):
        """Position the toolbar based on configuration."""
        try:
            desktop = QDesktopWidget().availableGeometry()
            position = self.config.get('ui', 'position', 'top')
            
            # Set width to full screen width for horizontal positions
            if position in ['top', 'bottom']:
                self.setFixedWidth(desktop.width())
                self.setMinimumHeight(40)
            else:
                # For vertical positions
                self.setFixedHeight(desktop.height())
                self.setMinimumWidth(40)
            
            # Position the toolbar
            if position == 'top':
                self.move(0, 0)
            elif position == 'bottom':
                self.move(0, desktop.height() - self.height())
            elif position == 'left':
                self.move(0, 0)
            elif position == 'right':
                self.move(desktop.width() - self.width(), 0)
                
            # Log position
            logging.debug(f"Toolbar positioned at: {position}, coords: {self.pos().x()}, {self.pos().y()}, size: {self.width()}x{self.height()}")
            
        except Exception as e:
            warnings.warn(f"Error positioning toolbar: {e}")
            # Default positioning at top
            self.move(0, 0)
    
    def add_default_prompts(self):
        """Add default prompts to the toolbar for quick access."""
        # Get templates from the template manager
        templates = self.template_manager.get_templates()
        
        # Add up to 5 templates as quick access buttons
        for i, template in enumerate(templates[:5]):
            # Create a button for this template
            button = QPushButton()
            button.setText(template.name)
            button.setToolTip(f"Use template: {template.name}")
            button.clicked.connect(lambda checked=False, t=template: self.use_template(t))
            
            # Add to toolbar
            self.toolbar_layout.addWidget(button)
    
    def use_template(self, template):
        """Use a prompt template."""
        # Fill the template
        filled_content = template.fill_template()
        
        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(filled_content)
        
        # Show a message
        QMessageBox.information(self, "Template Used", 
                               f"Template '{template.name}' has been copied to clipboard.")
    
    def setup_prompt_shortcuts(self):
        """Set up keyboard shortcuts for prompt templates."""
        # Clear existing shortcuts
        for shortcut in self.shortcuts.values():
            shortcut.setEnabled(False)
            shortcut.deleteLater()
        self.shortcuts = {}
        
        # Create shortcuts for templates with defined shortcuts
        for template in self.template_manager.get_templates():
            if template.shortcut:
                try:
                    shortcut = QShortcut(QKeySequence(template.shortcut), self)
                    shortcut.activated.connect(lambda t=template: self.use_template(t))
                    self.shortcuts[template.name] = shortcut
                except Exception as e:
                    warnings.warn(f"Failed to create shortcut for template '{template.name}': {e}")
    
    def show_prompt_templates(self):
        """Show the prompt templates dialog."""
        dialog = PromptTemplatingDialog(self.template_manager, self)
        dialog.template_selected.connect(self.use_template)
        dialog.exec_()
        
        # Update shortcuts after dialog closes
        self.setup_prompt_shortcuts()
    
    def show_github_settings(self):
        """Show the GitHub settings dialog."""
        if not self.github_plugin:
            QMessageBox.warning(self, "Error", "GitHub plugin not loaded.")
            return
            
        from Toolbar.ui.github_settings import GitHubSettingsDialog
        dialog = GitHubSettingsDialog(self.github_plugin.monitor, self)
        dialog.exec_()
    
    def show_linear_settings(self):
        """Show the Linear settings dialog."""
        if not self.linear_plugin:
            QMessageBox.warning(self, "Error", "Linear plugin not loaded.")
            return
            
        from Toolbar.ui.linear_settings import LinearSettingsDialog
        dialog = LinearSettingsDialog(self.linear_plugin.integration, self)
        dialog.exec_()
    
    def show_projects_dialog(self):
        """Show the GitHub projects dialog."""
        dialog = GitHubProjectsDialog(self.github_plugin.monitor, self)
        if dialog.exec_():
            # Reload pinned projects
            if self.github_ui:
                self.github_ui.load_pinned_projects()
    
    def show_toolbar_settings(self):
        """Show the toolbar settings dialog."""
        dialog = ToolbarSettingsDialog(self.config, self)
        if dialog.exec_():
            # Apply settings
            self.apply_settings()
    
    def apply_settings(self):
        """Apply settings from configuration."""
        try:
            # Set opacity to 1.0 (fully opaque) if not specified
            opacity = float(self.config.get('ui', 'opacity', 1.0))
            self.setWindowOpacity(opacity)
            
            # Set position
            self.position_toolbar()
            
            # Set stay on top and ensure proper window flags
            try:
                stay_on_top = self.config.get('ui', 'stay_on_top', True)
                # Reset window flags
                flags = Qt.FramelessWindowHint | Qt.Tool
                if stay_on_top:
                    flags |= Qt.WindowStaysOnTopHint
                self.setWindowFlags(flags)
            except Exception as e:
                warnings.warn(f"Error setting window flags: {e}")
                # Default to basic flags
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
            
            # Force visibility
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            
            # Show the window to apply changes and ensure it's at the top
            self.show()
            self.raise_() # Bring window to front
            self.activateWindow() # Set as active window
            
            # Log position
            logging.debug(f"Toolbar positioned at: {self.pos().x()}, {self.pos().y()}, size: {self.width()}x{self.height()}")
        except Exception as e:
            warnings.warn(f"Error applying settings: {e}")
            # Make sure window is visible even if settings fail
            self.show()
            self.raise_()
            self.activateWindow()
    
    def show_toolbar_context_menu(self, position):
        """Show context menu for the toolbar."""
        menu = QMenu()
        
        # Add script action
        add_script_action = menu.addAction("Add Script")
        add_script_action.triggered.connect(self.add_script)
        
        # Settings action
        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self.show_toolbar_settings)
        
        # Exit action
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Show menu at cursor position
        menu.exec_(QCursor.pos())
    
    def add_script_button(self, script_data):
        """Add a button to the toolbar for a script."""
        # Create a button
        button = QPushButton()
        button.setText(script_data.get('name', 'Script'))
        button.setToolTip(script_data.get('description', ''))
        
        # Connect to the run_script method
        script_path = script_data.get('path', '')
        button.clicked.connect(lambda: self.run_script(script_path))
        
        # Set context menu policy
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        button.customContextMenuRequested.connect(
            lambda pos, b=button, p=script_path: self.show_script_context_menu(pos, b, p)
        )
        
        # Add to the toolbar
        self.toolbar_layout.addWidget(button)
        
        # Add to the scripts dictionary for tracking
        self.script_buttons[script_path] = button
        
        return button
    
    def show_script_context_menu(self, position, button, path):
        """
        Show context menu for a script button.
        
        Args:
            position (QPoint): Position where the menu should be shown
            button (QPushButton): The script button
            path (str): Path to the script
        """
        menu = QMenu()
        
        # Edit script action
        edit_action = menu.addAction("Edit Script")
        edit_action.triggered.connect(lambda: self.edit_script(path))
        
        # Change icon action
        change_icon_action = menu.addAction("Change Icon")
        change_icon_action.triggered.connect(lambda: self.change_script_icon(button, path))
        
        # Remove script action
        remove_action = menu.addAction("Remove Script")
        remove_action.triggered.connect(lambda: self.delete_script(button, path))
        
        # Show menu at cursor position
        menu.exec_(button.mapToGlobal(position))
    
    def add_script(self):
        """Add a script to the toolbar."""
        # Get script path
        script_path, _ = QFileDialog.getOpenFileName(
            self, "Select Script", "", "All Files (*)"
        )
        
        if script_path:
            # Get script name
            script_name, ok = QInputDialog.getText(
                self, "Script Name", "Enter a name for the script:"
            )
            
            if ok and script_name:
                # Add script to manager
                script_data = self.script_manager.add_script(script_path, script_name)
                
                # Add button to toolbar
                self.add_script_button(script_data)
    
    def run_script(self, path):
        """
        Run a script.
        
        Args:
            path (str): Path to the script
        """
        self.script_manager.run_script(path)
    
    def edit_script(self, path):
        """
        Edit a script.
        
        Args:
            path (str): Path to the script
        """
        self.script_manager.edit_script(path)
    
    def change_script_icon(self, button, path):
        """
        Change the icon of a script.
        
        Args:
            button (QPushButton): The script button
            path (str): Path to the script
        """
        icon_path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon", "", "Image Files (*.png *.jpg *.svg)"
        )
        
        if icon_path:
            # Update icon
            button.setIcon(QIcon(icon_path))
            
            # Update script data
            self.script_manager.update_script_icon(path, icon_path)
    
    def delete_script(self, button, path):
        """
        Delete a script.
        
        Args:
            button (QPushButton): The script button
            path (str): Path to the script
        """
        confirm = QMessageBox.question(
            self, "Confirm Deletion", "Are you sure you want to delete this script?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Remove button from toolbar
            button.setParent(None)
            button.deleteLater()
            
            # Delete script
            self.script_manager.delete_script(path)
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop GitHub monitoring if available
        if self.github_plugin:
            self.github_plugin.stop_monitoring()
            
            # Save projects
            try:
                self.github_plugin.save_projects()
            except Exception as e:
                warnings.warn(f"Failed to save projects: {e}")
        
        # Accept the event
        event.accept()
