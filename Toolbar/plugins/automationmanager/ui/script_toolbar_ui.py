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

from Toolbar.plugins.automationmanager.script_manager import ScriptManager
from Toolbar.plugins.templateprompt.prompt_templating import PromptTemplateManager
from Toolbar.plugins.templateprompt.ui.prompt_templating_ui import PromptTemplatingDialog
from Toolbar.ui.toolbar_settings import ToolbarSettingsDialog
from toolkit.plugins.github.ui.github_settings import GitHubSettingsDialog
from Toolbar.plugins.linear.linear_settings import LinearSettingsDialog
from toolkit.plugins.github.ui.github_project_ui import GitHubProjectsDialog
from toolkit.plugins.github.ui.github_ui import GitHubUI

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
