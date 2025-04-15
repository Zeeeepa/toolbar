import os
import sys
import logging
import re
from typing import Dict, List, Optional, Any

from PyQt5.QtWidgets import (
    QMainWindow, QToolBar, QAction, QFileDialog, QInputDialog, QMenu, 
    QMessageBox, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QShortcut, 
    QDesktopWidget, QToolButton, QApplication, QSizePolicy, QPushButton,
    QTabWidget, QSplitter, QTreeView, QListWidget, QListWidgetItem, QDialog,
    QLineEdit, QComboBox, QCheckBox, QGroupBox, QScrollArea, QTextEdit
)
from PyQt5.QtGui import QIcon, QCursor, QKeySequence, QColor, QPalette, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, QModelIndex, QRect

# Import from Toolbar modules
from Toolbar.ui.toolbar_settings import ToolbarSettingsDialog
from Toolbar.ui.notification_widget import NotificationWidget

logger = logging.getLogger(__name__)

class Toolbar(QMainWindow):
    """
    Main toolbar window with enhanced GitHub project management.
    This class provides a robust interface that continues to function
    even if some plugins fail to load.
    """
    
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
        self.plugins = {}
        self.plugin_uis = {}
        self.github_ui = None
        self.github_projects_dialog = None
        self.linear_ui = None
        
        # Set window properties
        self.setWindowTitle("Toolbar")
        
        # Get position and opacity from config
        self.position = self.config.get('ui', 'position', 'top')
        self.opacity = float(self.config.get('ui', 'opacity', 0.9))
        self.stay_on_top = self.config.get('ui', 'stay_on_top', True)
        
        # Set window flags based on configuration
        self._update_window_flags()
        
        # Set window opacity
        self.setWindowOpacity(self.opacity)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout based on position
        self._create_layout()
        
        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        
        # Add toolbar to appropriate position
        if self.position in ['top', 'bottom']:
            self.addToolBar(Qt.TopToolBarArea if self.position == 'top' else Qt.BottomToolBarArea, self.toolbar)
        else:
            self.addToolBar(Qt.LeftToolBarArea if self.position == 'left' else Qt.RightToolBarArea, self.toolbar)
        
        # Create status bar
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Initialize UI components
        self._init_ui()
        
        # Load plugins
        self._load_plugins()
        
        # Position the toolbar
        self._position_toolbar()
        
        # Set up auto-save timer
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(60000)  # Save every minute
        
        logger.info("Toolbar initialized")
    
    def _update_window_flags(self):
        """Update window flags based on configuration."""
        flags = Qt.Tool  # Base flag for toolbar-like window
        
        if self.stay_on_top:
            flags |= Qt.WindowStaysOnTopHint
        
        self.setWindowFlags(flags)
    
    def _create_layout(self):
        """Create the main layout based on position."""
        if self.position in ['top', 'bottom']:
            # Horizontal layout for top/bottom positions
            self.main_layout = QVBoxLayout(self.central_widget)
            self.setMinimumSize(800, 50)
        else:
            # Vertical layout for left/right positions
            self.main_layout = QHBoxLayout(self.central_widget)
            self.setMinimumSize(50, 600)
        
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(2)
    
    def _init_ui(self):
        """Initialize the UI components."""
        try:
            # Create main tab widget
            self.tab_widget = QTabWidget()
            
            # Set tab position based on toolbar position
            if self.position == 'bottom':
                self.tab_widget.setTabPosition(QTabWidget.South)
            elif self.position == 'left':
                self.tab_widget.setTabPosition(QTabWidget.West)
            elif self.position == 'right':
                self.tab_widget.setTabPosition(QTabWidget.East)
            else:  # default to top
                self.tab_widget.setTabPosition(QTabWidget.North)
            
            self.main_layout.addWidget(self.tab_widget)
            
            # Create GitHub tab
            self.github_tab = QWidget()
            self.github_layout = QVBoxLayout(self.github_tab)
            self.tab_widget.addTab(self.github_tab, "GitHub")
            
            # Create GitHub toolbar
            self.github_toolbar = QToolBar()
            self.github_layout.addWidget(self.github_toolbar)
            
            # Add GitHub actions
            self.refresh_action = QAction(QIcon.fromTheme("view-refresh"), "Refresh", self)
            self.refresh_action.triggered.connect(self._refresh_github)
            self.github_toolbar.addAction(self.refresh_action)
            
            self.new_pr_action = QAction(QIcon.fromTheme("document-new"), "New PR", self)
            self.new_pr_action.triggered.connect(self._create_new_pr)
            self.github_toolbar.addAction(self.new_pr_action)
            
            self.view_prs_action = QAction(QIcon.fromTheme("document-open"), "View PRs", self)
            self.view_prs_action.triggered.connect(self._view_prs)
            self.github_toolbar.addAction(self.view_prs_action)
            
            self.new_branch_action = QAction(QIcon.fromTheme("document-new"), "New Branch", self)
            self.new_branch_action.triggered.connect(self._create_new_branch)
            self.github_toolbar.addAction(self.new_branch_action)
            
            self.github_toolbar.addSeparator()
            
            self.settings_action = QAction(QIcon.fromTheme("preferences-system"), "Settings", self)
            self.settings_action.triggered.connect(self._show_settings)
            self.github_toolbar.addAction(self.settings_action)
            
            # Create GitHub content area
            self.github_content = QSplitter(Qt.Horizontal)
            self.github_layout.addWidget(self.github_content)
            
            # Create repository tree view
            self.repo_tree = QTreeView()
            self.repo_model = QStandardItemModel()
            self.repo_model.setHorizontalHeaderLabels(["Repositories"])
            self.repo_tree.setModel(self.repo_model)
            self.github_content.addWidget(self.repo_tree)
            
            # Create PR list view
            self.pr_list = QListWidget()
            self.github_content.addWidget(self.pr_list)
            
            # Create PR details view
            self.pr_details = QTextEdit()
            self.pr_details.setReadOnly(True)
            self.github_content.addWidget(self.pr_details)
            
            # Set splitter sizes
            self.github_content.setSizes([200, 300, 500])
            
            # Create Linear tab
            self.linear_tab = QWidget()
            self.linear_layout = QVBoxLayout(self.linear_tab)
            self.tab_widget.addTab(self.linear_tab, "Linear")
            
            # Create Linear toolbar
            self.linear_toolbar = QToolBar()
            self.linear_layout.addWidget(self.linear_toolbar)
            
            # Add Linear actions
            self.refresh_linear_action = QAction(QIcon.fromTheme("view-refresh"), "Refresh", self)
            self.refresh_linear_action.triggered.connect(self._refresh_linear)
            self.linear_toolbar.addAction(self.refresh_linear_action)
            
            self.new_issue_action = QAction(QIcon.fromTheme("document-new"), "New Issue", self)
            self.new_issue_action.triggered.connect(self._create_new_issue)
            self.linear_toolbar.addAction(self.new_issue_action)
            
            self.view_issues_action = QAction(QIcon.fromTheme("document-open"), "View Issues", self)
            self.view_issues_action.triggered.connect(self._view_issues)
            self.linear_toolbar.addAction(self.view_issues_action)
            
            self.linear_toolbar.addSeparator()
            
            self.linear_settings_action = QAction(QIcon.fromTheme("preferences-system"), "Settings", self)
            self.linear_settings_action.triggered.connect(self._show_linear_settings)
            self.linear_toolbar.addAction(self.linear_settings_action)
            
            # Create Linear content area
            self.linear_content = QSplitter(Qt.Horizontal)
            self.linear_layout.addWidget(self.linear_content)
            
            # Create team/project tree view
            self.team_tree = QTreeView()
            self.team_model = QStandardItemModel()
            self.team_model.setHorizontalHeaderLabels(["Teams & Projects"])
            self.team_tree.setModel(self.team_model)
            self.linear_content.addWidget(self.team_tree)
            
            # Create issue list view
            self.issue_list = QListWidget()
            self.linear_content.addWidget(self.issue_list)
            
            # Create issue details view
            self.issue_details = QTextEdit()
            self.issue_details.setReadOnly(True)
            self.linear_content.addWidget(self.issue_details)
            
            # Set splitter sizes
            self.linear_content.setSizes([200, 300, 500])
            
            # Create Plugins tab
            self.plugins_tab = QWidget()
            self.plugins_layout = QVBoxLayout(self.plugins_tab)
            self.tab_widget.addTab(self.plugins_tab, "Plugins")
            
            # Create plugins list
            self.plugins_list = QListWidget()
            self.plugins_layout.addWidget(self.plugins_list)
            
            # Create plugin details
            self.plugin_details = QTextEdit()
            self.plugin_details.setReadOnly(True)
            self.plugins_layout.addWidget(self.plugin_details)
            
            # Connect signals
            self.plugins_list.currentItemChanged.connect(self._show_plugin_details)
            self.repo_tree.clicked.connect(self._repo_selected)
            self.pr_list.currentItemChanged.connect(self._pr_selected)
            self.team_tree.clicked.connect(self._team_selected)
            self.issue_list.currentItemChanged.connect(self._issue_selected)
            
            logger.info("UI components initialized")
        except Exception as e:
            logger.error(f"Error initializing UI: {e}", exc_info=True)
            raise
    
    def _load_plugins(self):
        """Load and initialize plugins."""
        try:
            # Get all loaded plugins
            self.plugins = self.plugin_manager.get_all_plugins()
            
            # Update plugins list
            self.plugins_list.clear()
            for name, plugin in self.plugins.items():
                item = QListWidgetItem(f"{name} v{plugin.version}")
                item.setData(Qt.UserRole, name)
                self.plugins_list.addItem(item)
            
            # Initialize plugin UIs
            for name, plugin in self.plugins.items():
                try:
                    if hasattr(plugin, "get_ui"):
                        ui = plugin.get_ui(self)
                        if ui:
                            self.plugin_uis[name] = ui
                            
                            # Check for specific plugins
                            if name == "GitHubPlugin":
                                self.github_ui = ui
                            elif name == "LinearPlugin":
                                self.linear_ui = ui
                except Exception as e:
                    logger.error(f"Error initializing UI for plugin {name}: {e}", exc_info=True)
            
            logger.info(f"Loaded {len(self.plugins)} plugins")
        except Exception as e:
            logger.error(f"Error loading plugins: {e}", exc_info=True)
    
    def _position_toolbar(self):
        """Position the toolbar on the screen based on settings."""
        try:
            # Get screen geometry
            screen = QDesktopWidget().screenGeometry()
            
            # Calculate position based on toolbar position setting
            if self.position == "top":
                x = (screen.width() - self.width()) // 2
                y = 0
                self.setGeometry(x, y, self.width(), self.height())
            elif self.position == "bottom":
                x = (screen.width() - self.width()) // 2
                y = screen.height() - self.height()
                self.setGeometry(x, y, self.width(), self.height())
            elif self.position == "left":
                x = 0
                y = (screen.height() - self.height()) // 2
                self.setGeometry(x, y, self.width(), self.height())
            elif self.position == "right":
                x = screen.width() - self.width()
                y = (screen.height() - self.height()) // 2
                self.setGeometry(x, y, self.width(), self.height())
            else:
                # Default to center
                x = (screen.width() - self.width()) // 2
                y = (screen.height() - self.height()) // 2
                self.setGeometry(x, y, self.width(), self.height())
            
            logger.info(f"Positioned toolbar at {self.geometry().x()}, {self.geometry().y()}, {self.width()}x{self.height()}")
        except Exception as e:
            logger.error(f"Error positioning toolbar: {e}", exc_info=True)
    
    def _auto_save(self):
        """Auto-save configuration."""
        try:
            self.config.save_config()
            logger.debug("Configuration auto-saved")
        except Exception as e:
            logger.error(f"Error auto-saving configuration: {e}", exc_info=True)
    
    def _repo_selected(self, index):
        """Handle repository selection."""
        try:
            # Get repository data
            item = self.repo_model.itemFromIndex(index)
            repo_data = item.data(Qt.UserRole)
            
            if repo_data:
                # Update PR list
                self.pr_list.clear()
                
                # Update status
                self.status_label.setText(f"Selected repository: {repo_data['name']}")
                
                logger.info(f"Repository selected: {repo_data['name']}")
        except Exception as e:
            logger.error(f"Error handling repository selection: {e}", exc_info=True)
    
    def _pr_selected(self, current, previous):
        """Handle PR selection."""
        try:
            if current:
                # Get PR data
                pr = current.data(Qt.UserRole)
                
                # Update PR details
                self.pr_details.setHtml(f"""
                    <h2>#{pr['number']} - {pr['title']}</h2>
                    <p><b>Author:</b> {pr['user']['login']}</p>
                    <p><b>Created:</b> {pr['created_at']}</p>
                    <p><b>Status:</b> {pr['state']}</p>
                    <p><b>Description:</b></p>
                    <div>{pr['body']}</div>
                """)
                
                # Update status
                self.status_label.setText(f"Selected PR: #{pr['number']} - {pr['title']}")
                
                logger.info(f"PR selected: #{pr['number']} - {pr['title']}")
        except Exception as e:
            logger.error(f"Error handling PR selection: {e}", exc_info=True)
    
    def _team_selected(self, index):
        """Handle team/project selection."""
        try:
            # Get team/project data
            item = self.team_model.itemFromIndex(index)
            data = item.data(Qt.UserRole)
            
            # Update status
            if "type" in data and data["type"] == "team":
                self.status_label.setText(f"Selected team: {data['name']}")
                logger.info(f"Team selected: {data['name']}")
            elif "type" in data and data["type"] == "project":
                self.status_label.setText(f"Selected project: {data['name']}")
                logger.info(f"Project selected: {data['name']}")
        except Exception as e:
            logger.error(f"Error handling team/project selection: {e}", exc_info=True)
    
    def _issue_selected(self, current, previous):
        """Handle issue selection."""
        try:
            if current:
                # Get issue data
                issue = current.data(Qt.UserRole)
                
                # Update issue details
                self.issue_details.setHtml(f"""
                    <h2>{issue['identifier']} - {issue['title']}</h2>
                    <p><b>Assignee:</b> {issue['assignee']['name'] if issue['assignee'] else 'Unassigned'}</p>
                    <p><b>Status:</b> {issue['state']['name']}</p>
                    <p><b>Priority:</b> {issue['priority']}</p>
                    <p><b>Description:</b></p>
                    <div>{issue['description']}</div>
                """)
                
                # Update status
                self.status_label.setText(f"Selected issue: {issue['identifier']} - {issue['title']}")
                
                logger.info(f"Issue selected: {issue['identifier']} - {issue['title']}")
        except Exception as e:
            logger.error(f"Error handling issue selection: {e}", exc_info=True)
    
    def _show_plugin_details(self, current, previous):
        """Show plugin details."""
        try:
            if current:
                # Get plugin name
                name = current.data(Qt.UserRole)
                
                # Get plugin
                plugin = self.plugins.get(name)
                
                if plugin:
                    # Update plugin details
                    self.plugin_details.setHtml(f"""
                        <h2>{name} v{plugin.version}</h2>
                        <p><b>Description:</b> {plugin.description}</p>
                        <p><b>Status:</b> Active</p>
                    """)
                    
                    logger.info(f"Plugin details shown for {name}")
        except Exception as e:
            logger.error(f"Error showing plugin details: {e}", exc_info=True)
    
    def _refresh_github(self):
        """Refresh GitHub data."""
        try:
            if self.github_ui:
                self.github_ui.refresh_repositories()
                self.status_label.setText("GitHub data refreshed")
                logger.info("GitHub data refreshed")
            else:
                QMessageBox.warning(self, "GitHub Plugin Not Available", 
                                   "The GitHub plugin is not available. Please check the plugin status.")
                logger.warning("GitHub plugin not available for refresh")
        except Exception as e:
            logger.error(f"Error refreshing GitHub data: {e}", exc_info=True)
            QMessageBox.critical(self, "Refresh Error", f"Error refreshing GitHub data: {str(e)}")
    
    def _create_new_pr(self):
        """Create a new GitHub PR."""
        try:
            if self.github_ui:
                self.github_ui.create_pr()
                logger.info("New PR creation initiated")
            else:
                QMessageBox.warning(self, "GitHub Plugin Not Available", 
                                   "The GitHub plugin is not available. Please check the plugin status.")
                logger.warning("GitHub plugin not available for PR creation")
        except Exception as e:
            logger.error(f"Error creating new PR: {e}", exc_info=True)
            QMessageBox.critical(self, "PR Creation Error", f"Error creating new PR: {str(e)}")
    
    def _view_prs(self):
        """View GitHub PRs."""
        try:
            if self.github_ui:
                self.github_ui.view_prs()
                logger.info("View PRs initiated")
            else:
                QMessageBox.warning(self, "GitHub Plugin Not Available", 
                                   "The GitHub plugin is not available. Please check the plugin status.")
                logger.warning("GitHub plugin not available for viewing PRs")
        except Exception as e:
            logger.error(f"Error viewing PRs: {e}", exc_info=True)
            QMessageBox.critical(self, "View PRs Error", f"Error viewing PRs: {str(e)}")
    
    def _create_new_branch(self):
        """Create a new GitHub branch."""
        try:
            if self.github_ui:
                self.github_ui.create_branch()
                logger.info("New branch creation initiated")
            else:
                QMessageBox.warning(self, "GitHub Plugin Not Available", 
                                   "The GitHub plugin is not available. Please check the plugin status.")
                logger.warning("GitHub plugin not available for branch creation")
        except Exception as e:
            logger.error(f"Error creating new branch: {e}", exc_info=True)
            QMessageBox.critical(self, "Branch Creation Error", f"Error creating new branch: {str(e)}")
    
    def _refresh_linear(self):
        """Refresh Linear data."""
        try:
            if "LinearPlugin" in self.plugins:
                # Refresh Linear data
                self.status_label.setText("Linear data refreshed")
                logger.info("Linear data refreshed")
            else:
                QMessageBox.warning(self, "Linear Plugin Not Available", 
                                   "The Linear plugin is not available. Please check the plugin status.")
                logger.warning("Linear plugin not available for refresh")
        except Exception as e:
            logger.error(f"Error refreshing Linear data: {e}", exc_info=True)
            QMessageBox.critical(self, "Refresh Error", f"Error refreshing Linear data: {str(e)}")
    
    def _create_new_issue(self):
        """Create a new Linear issue."""
        try:
            if "LinearPlugin" in self.plugins:
                # Create new issue
                logger.info("New issue creation initiated")
            else:
                QMessageBox.warning(self, "Linear Plugin Not Available", 
                                   "The Linear plugin is not available. Please check the plugin status.")
                logger.warning("Linear plugin not available for issue creation")
        except Exception as e:
            logger.error(f"Error creating new issue: {e}", exc_info=True)
            QMessageBox.critical(self, "Issue Creation Error", f"Error creating new issue: {str(e)}")
    
    def _view_issues(self):
        """View Linear issues."""
        try:
            if "LinearPlugin" in self.plugins:
                # View issues
                logger.info("View issues initiated")
            else:
                QMessageBox.warning(self, "Linear Plugin Not Available", 
                                   "The Linear plugin is not available. Please check the plugin status.")
                logger.warning("Linear plugin not available for viewing issues")
        except Exception as e:
            logger.error(f"Error viewing issues: {e}", exc_info=True)
            QMessageBox.critical(self, "View Issues Error", f"Error viewing issues: {str(e)}")
    
    def _show_settings(self):
        """Show settings dialog."""
        try:
            settings_dialog = ToolbarSettingsDialog(self.config, self)
            if settings_dialog.exec_():
                # Apply settings if dialog was accepted
                self._apply_settings()
            logger.info("Settings dialog shown")
        except Exception as e:
            logger.error(f"Error showing settings dialog: {e}", exc_info=True)
            QMessageBox.critical(self, "Settings Error", f"Error showing settings dialog: {str(e)}")
    
    def _apply_settings(self):
        """Apply settings from configuration."""
        try:
            # Get updated settings
            new_position = self.config.get('ui', 'position', 'top')
            new_opacity = float(self.config.get('ui', 'opacity', 0.9))
            new_stay_on_top = self.config.get('ui', 'stay_on_top', True)
            
            # Check if position changed
            position_changed = new_position != self.position
            
            # Update instance variables
            self.position = new_position
            self.opacity = new_opacity
            self.stay_on_top = new_stay_on_top
            
            # Apply opacity
            self.setWindowOpacity(self.opacity)
            
            # Update window flags
            self._update_window_flags()
            
            # If position changed, recreate the layout
            if position_changed:
                # Store the current size
                current_size = self.size()
                
                # Remove all widgets from the layout
                while self.main_layout.count():
                    item = self.main_layout.takeAt(0)
                    if item.widget():
                        item.widget().setParent(None)
                
                # Recreate the layout
                self._create_layout()
                
                # Re-add the tab widget
                self.main_layout.addWidget(self.tab_widget)
                
                # Update tab position
                if self.position == 'bottom':
                    self.tab_widget.setTabPosition(QTabWidget.South)
                elif self.position == 'left':
                    self.tab_widget.setTabPosition(QTabWidget.West)
                elif self.position == 'right':
                    self.tab_widget.setTabPosition(QTabWidget.East)
                else:  # default to top
                    self.tab_widget.setTabPosition(QTabWidget.North)
                
                # Reposition the toolbar
                self._position_toolbar()
            
            logger.info(f"Applied settings: position={self.position}, opacity={self.opacity}, stay_on_top={self.stay_on_top}")
        except Exception as e:
            logger.error(f"Error applying settings: {e}", exc_info=True)
            QMessageBox.critical(self, "Settings Error", f"Error applying settings: {str(e)}")
    
    def _show_linear_settings(self):
        """Show Linear settings dialog."""
        try:
            if self.linear_ui:
                self.linear_ui.exec_()
                logger.info("Linear settings dialog shown")
            else:
                QMessageBox.warning(self, "Linear Plugin Not Available", 
                                   "The Linear plugin is not available. Please check the plugin status.")
                logger.warning("Linear plugin not available for settings")
        except Exception as e:
            logger.error(f"Error showing Linear settings dialog: {e}", exc_info=True)
            QMessageBox.critical(self, "Linear Settings Error", f"Error showing Linear settings dialog: {str(e)}")
    
    def closeEvent(self, event):
        """Handle close event."""
        try:
            # Save configuration
            self.config.save_config()
            
            # Clean up plugins
            for name, plugin in self.plugins.items():
                try:
                    if hasattr(plugin, "cleanup"):
                        plugin.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up plugin {name}: {e}", exc_info=True)
            
            logger.info("Toolbar closed")
            event.accept()
        except Exception as e:
            logger.error(f"Error during close event: {e}", exc_info=True)
            event.accept()
