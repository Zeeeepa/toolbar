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
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, QModelIndex

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
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setMinimumSize(800, 50)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(2)
        
        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.toolbar)
        
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
    
    def _init_ui(self):
        """Initialize the UI components."""
        try:
            # Create main tab widget
            self.tab_widget = QTabWidget()
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
            
            # Initialize GitHub UI if available
            if "GitHubPlugin" in self.plugins:
                try:
                    from Toolbar.plugins.github.ui.github_ui import GitHubUI
                    from Toolbar.plugins.github.ui.github_project_ui import GitHubProjectsDialog
                    
                    self.github_ui = GitHubUI(self.plugins["GitHubPlugin"], self)
                    self.github_projects_dialog = GitHubProjectsDialog(self.plugins["GitHubPlugin"], self)
                    
                    # Connect GitHub UI signals
                    self._connect_github_signals()
                    
                    logger.info("GitHub UI initialized")
                except Exception as e:
                    logger.error(f"Error initializing GitHub UI: {e}", exc_info=True)
            
            # Initialize Linear UI if available
            if "LinearPlugin" in self.plugins:
                try:
                    from Toolbar.plugins.linear.linear_settings import LinearSettingsDialog
                    
                    self.linear_ui = LinearSettingsDialog(self.config, self)
                    
                    logger.info("Linear UI initialized")
                except Exception as e:
                    logger.error(f"Error initializing Linear UI: {e}", exc_info=True)
            
            # Initialize other plugin UIs
            for name, plugin in self.plugins.items():
                if name not in ["GitHubPlugin", "LinearPlugin"]:
                    try:
                        if hasattr(plugin, "get_ui"):
                            ui = plugin.get_ui(self)
                            if ui:
                                self.plugin_uis[name] = ui
                                logger.info(f"UI for plugin {name} initialized")
                    except Exception as e:
                        logger.error(f"Error initializing UI for plugin {name}: {e}", exc_info=True)
            
            logger.info("Plugins loaded")
        except Exception as e:
            logger.error(f"Error loading plugins: {e}", exc_info=True)
            raise
    
    def _position_toolbar(self):
        """Position the toolbar on the screen."""
        try:
            # Get screen geometry
            screen = QDesktopWidget().screenGeometry()
            
            # Get toolbar geometry
            toolbar_geometry = self.geometry()
            
            # Position at the top center of the screen
            x = (screen.width() - toolbar_geometry.width()) // 2
            y = 0
            
            # Set position
            self.move(x, y)
            
            logger.info(f"Toolbar positioned at ({x}, {y})")
        except Exception as e:
            logger.error(f"Error positioning toolbar: {e}", exc_info=True)
    
    def _auto_save(self):
        """Auto-save configuration."""
        try:
            # Save configuration
            self.config.save()
            logger.debug("Configuration auto-saved")
        except Exception as e:
            logger.error(f"Error auto-saving configuration: {e}", exc_info=True)
    
    def _connect_github_signals(self):
        """Connect GitHub UI signals."""
        if self.github_ui:
            try:
                # Connect signals
                self.github_ui.repositories_updated.connect(self._update_repo_tree)
                self.github_ui.prs_updated.connect(self._update_pr_list)
                
                logger.info("GitHub signals connected")
            except Exception as e:
                logger.error(f"Error connecting GitHub signals: {e}", exc_info=True)
    
    def _update_repo_tree(self, repos):
        """Update repository tree view."""
        try:
            # Clear model
            self.repo_model.clear()
            self.repo_model.setHorizontalHeaderLabels(["Repositories"])
            
            # Add repositories
            for repo in repos:
                item = QStandardItem(repo["name"])
                item.setData(repo, Qt.UserRole)
                self.repo_model.appendRow(item)
            
            logger.info(f"Repository tree updated with {len(repos)} repositories")
        except Exception as e:
            logger.error(f"Error updating repository tree: {e}", exc_info=True)
    
    def _update_pr_list(self, prs):
        """Update PR list view."""
        try:
            # Clear list
            self.pr_list.clear()
            
            # Add PRs
            for pr in prs:
                item = QListWidgetItem(f"#{pr['number']} - {pr['title']}")
                item.setData(Qt.UserRole, pr)
                self.pr_list.addItem(item)
            
            logger.info(f"PR list updated with {len(prs)} PRs")
        except Exception as e:
            logger.error(f"Error updating PR list: {e}", exc_info=True)
    
    def _repo_selected(self, index):
        """Handle repository selection."""
        try:
            # Get repository data
            item = self.repo_model.itemFromIndex(index)
            repo = item.data(Qt.UserRole)
            
            # Update status
            self.status_label.setText(f"Selected repository: {repo['name']}")
            
            # Refresh PRs for this repository
            if self.github_ui:
                self.github_ui.refresh_prs(repo["name"])
            
            logger.info(f"Repository selected: {repo['name']}")
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
            settings_dialog.exec_()
            logger.info("Settings dialog shown")
        except Exception as e:
            logger.error(f"Error showing settings dialog: {e}", exc_info=True)
            QMessageBox.critical(self, "Settings Error", f"Error showing settings dialog: {str(e)}")
    
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
            self.config.save()
            
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
