import os
import sys
import json
import webbrowser
import re
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QComboBox, QPushButton, QToolButton, 
                            QMenu, QAction, QDialog, QFileDialog, QListWidget,
                            QListWidgetItem, QMessageBox, QTabWidget, QTextEdit,
                            QCheckBox, QGroupBox, QScrollArea, QSplitter)
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

from toolkit.plugins.github.ui.github_settings import GitHubSettingsDialog
from toolkit.plugins.github.ui.github_project_ui import GitHubProjectsDialog
from toolkit.plugins.github.ui.github_ui import GitHubUI

from Toolbar.plugins.automationmanager.script_manager import ScriptManager

class ScriptToolbarUI(QWidget):
    """UI component for script automation functionality."""
    
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
