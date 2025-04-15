#!/usr/bin/env python3
import os
import sys
import logging
import re
from typing import Dict, List, Optional, Any
import subprocess

from PyQt5.QtWidgets import (
    QMainWindow, QToolBar, QAction, QFileDialog, QInputDialog, QMenu, 
    QMessageBox, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QShortcut, 
    QDesktopWidget, QToolButton, QApplication, QSizePolicy, QPushButton,
    QTabWidget, QSplitter, QTreeView, QListWidget, QListWidgetItem, QDialog,
    QLineEdit, QComboBox, QCheckBox, QGroupBox, QScrollArea, QTextEdit,
    QSystemTrayIcon
)
from PyQt5.QtGui import QIcon, QCursor, QKeySequence, QColor, QPalette, QStandardItemModel, QStandardItem, QPixmap
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, QModelIndex, QPoint

# Import from toolkit modules
from toolkit.toolbar.ui.toolbar_settings import ToolbarSettingsDialog
from toolkit.toolbar.ui.notification_widget import NotificationWidget

logger = logging.getLogger(__name__)

class TaskbarButton(QToolButton):
    """
    A button representing an application in the taskbar.
    """
    def __init__(self, icon, title, parent=None):
        super().__init__(parent)
        self.setIcon(icon)
        self.setToolTip(title)
        self.setText(title)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIconSize(QSize(24, 24))
        self.setMinimumWidth(120)
        self.setMaximumWidth(200)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setStyleSheet("""
            QToolButton {
                border: 1px solid #555;
                border-radius: 3px;
                background-color: #333;
                color: #fff;
                padding: 4px;
                text-align: left;
            }
            QToolButton:hover {
                background-color: #444;
            }
            QToolButton:pressed {
                background-color: #222;
            }
        """)
        
        # Store application info
        self.app_path = None
        self.app_args = []
        self.process = None
        
    def set_application(self, path, args=None):
        """Set the application path and arguments."""
        self.app_path = path
        self.app_args = args or []
        
    def launch_application(self):
        """Launch the associated application."""
        if not self.app_path:
            return
            
        try:
            if self.process and self.process.poll() is None:
                # Application is already running, bring it to front
                # This is platform-specific and might need additional code
                logger.info(f"Application already running: {self.app_path}")
                return
                
            # Launch the application
            cmd = [self.app_path] + self.app_args
            self.process = subprocess.Popen(cmd)
            logger.info(f"Launched application: {self.app_path}")
        except Exception as e:
            logger.error(f"Error launching application: {e}", exc_info=True)
            QMessageBox.critical(self.parent(), "Launch Error", f"Error launching application: {str(e)}")

class Toolbar(QMainWindow):
    """
    Main taskbar-style toolbar that sits at the bottom of the screen.
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
        self.app_buttons = []
        
        # Set window properties
        self.setWindowTitle("Toolbar")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool | Qt.FramelessWindowHint)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(2)
        
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("applications-system", QIcon(":/icons/toolbar.png")))
        self.tray_icon.setToolTip("Toolbar")
        self.tray_icon.activated.connect(self._tray_icon_activated)
        
        # Create tray menu
        self.tray_menu = QMenu()
        self.settings_action = self.tray_menu.addAction("Settings")
        self.settings_action.triggered.connect(self._show_settings)
        self.tray_menu.addSeparator()
        self.quit_action = self.tray_menu.addAction("Quit")
        self.quit_action.triggered.connect(self.close)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
        
        # Create start menu button
        self.start_button = QPushButton()
        self.start_button.setIcon(QIcon.fromTheme("start-here", QIcon(":/icons/start.png")))
        self.start_button.setIconSize(QSize(32, 32))
        self.start_button.setFixedSize(40, 40)
        self.start_button.setToolTip("Start Menu")
        self.start_button.clicked.connect(self._show_start_menu)
        self.main_layout.addWidget(self.start_button)
        
        # Create separator
        separator = QWidget()
        separator.setFixedWidth(1)
        separator.setStyleSheet("background-color: #555;")
        self.main_layout.addWidget(separator)
        
        # Create taskbar area (scrollable)
        self.taskbar_widget = QWidget()
        self.taskbar_layout = QHBoxLayout(self.taskbar_widget)
        self.taskbar_layout.setContentsMargins(0, 0, 0, 0)
        self.taskbar_layout.setSpacing(4)
        self.taskbar_layout.addStretch(1)  # Push buttons to the left
        
        self.main_layout.addWidget(self.taskbar_widget)
        
        # Create notification area
        self.notification_area = QWidget()
        self.notification_layout = QHBoxLayout(self.notification_area)
        self.notification_layout.setContentsMargins(0, 0, 0, 0)
        self.notification_layout.setSpacing(2)
        
        # Add clock
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignCenter)
        self.clock_label.setStyleSheet("color: white; font-weight: bold;")
        self.notification_layout.addWidget(self.clock_label)
        
        # Add separator before notification area
        separator2 = QWidget()
        separator2.setFixedWidth(1)
        separator2.setStyleSheet("background-color: #555;")
        self.main_layout.addWidget(separator2)
        
        self.main_layout.addWidget(self.notification_area)
        
        # Set up clock timer
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)  # Update every second
        self._update_clock()  # Initial update
        
        # Load plugins
        self._load_plugins()
        
        # Add default applications
        self._add_default_applications()
        
        # Position the toolbar
        self._position_toolbar()
        
        # Set up auto-save timer
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(60000)  # Save every minute
        
        # Apply taskbar styling
        self._apply_taskbar_style()
        
        logger.info("Toolbar initialized")
    
    def _apply_taskbar_style(self):
        """Apply taskbar styling to make it look like a system taskbar."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #222;
                border-top: 1px solid #444;
            }
            QPushButton {
                border: 1px solid #555;
                border-radius: 3px;
                background-color: #333;
                color: #fff;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #444;
            }
            QPushButton:pressed {
                background-color: #222;
            }
            QLabel {
                color: #fff;
            }
        """)
    
    def _update_clock(self):
        """Update the clock in the notification area."""
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        self.clock_label.setText(current_time)
    
    def _tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def _show_start_menu(self):
        """Show the start menu."""
        menu = QMenu(self)
        
        # Add applications section
        apps_menu = menu.addMenu("Applications")
        
        # Add some common applications
        # These would typically come from scanning the system
        file_manager_action = apps_menu.addAction("File Manager")
        file_manager_action.triggered.connect(lambda: self._launch_application("explorer.exe" if sys.platform == "win32" else "xdg-open"))
        
        browser_action = apps_menu.addAction("Web Browser")
        browser_action.triggered.connect(lambda: self._launch_application("chrome" if sys.platform == "win32" else "xdg-open https://www.google.com"))
        
        terminal_action = apps_menu.addAction("Terminal")
        terminal_action.triggered.connect(lambda: self._launch_application("cmd.exe" if sys.platform == "win32" else "x-terminal-emulator"))
        
        # Add plugins section
        if self.plugins:
            menu.addSeparator()
            plugins_menu = menu.addMenu("Plugins")
            
            for name, plugin in self.plugins.items():
                plugin_action = plugins_menu.addAction(name)
                plugin_action.triggered.connect(lambda checked, p=plugin: self._activate_plugin(p))
        
        # Add settings and power options
        menu.addSeparator()
        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self._show_settings)
        
        menu.addSeparator()
        power_menu = menu.addMenu("Power")
        
        logout_action = power_menu.addAction("Log Out")
        logout_action.triggered.connect(self.close)
        
        # Show the menu at the appropriate position
        menu.exec_(self.mapToGlobal(self.start_button.pos() + QPoint(0, -menu.sizeHint().height())))
    
    def _launch_application(self, app_path, args=None):
        """Launch an application."""
        try:
            if args is None:
                args = []
                
            subprocess.Popen([app_path] + args)
            logger.info(f"Launched application: {app_path}")
        except Exception as e:
            logger.error(f"Error launching application: {e}", exc_info=True)
            QMessageBox.critical(self, "Launch Error", f"Error launching application: {str(e)}")
    
    def _activate_plugin(self, plugin):
        """Activate a plugin."""
        try:
            if hasattr(plugin, "activate"):
                plugin.activate()
            logger.info(f"Activated plugin: {plugin.name}")
        except Exception as e:
            logger.error(f"Error activating plugin: {e}", exc_info=True)
            QMessageBox.critical(self, "Plugin Error", f"Error activating plugin: {str(e)}")
    
    def _add_default_applications(self):
        """Add default applications to the taskbar."""
        # These would typically come from configuration or system scanning
        
        # Add File Explorer
        file_explorer = TaskbarButton(QIcon.fromTheme("system-file-manager", QIcon(":/icons/file-explorer.png")), "File Explorer", self)
        file_explorer.set_application("explorer.exe" if sys.platform == "win32" else "xdg-open")
        file_explorer.clicked.connect(file_explorer.launch_application)
        self.taskbar_layout.addWidget(file_explorer)
        self.app_buttons.append(file_explorer)
        
        # Add Web Browser
        browser = TaskbarButton(QIcon.fromTheme("web-browser", QIcon(":/icons/web-browser.png")), "Web Browser", self)
        browser.set_application("chrome" if sys.platform == "win32" else "xdg-open", ["https://www.google.com"])
        browser.clicked.connect(browser.launch_application)
        self.taskbar_layout.addWidget(browser)
        self.app_buttons.append(browser)
        
        # Add Terminal
        terminal = TaskbarButton(QIcon.fromTheme("utilities-terminal", QIcon(":/icons/terminal.png")), "Terminal", self)
        terminal.set_application("cmd.exe" if sys.platform == "win32" else "x-terminal-emulator")
        terminal.clicked.connect(terminal.launch_application)
        self.taskbar_layout.addWidget(terminal)
        self.app_buttons.append(terminal)
        
        # Add Text Editor
        editor = TaskbarButton(QIcon.fromTheme("accessories-text-editor", QIcon(":/icons/text-editor.png")), "Text Editor", self)
        editor.set_application("notepad.exe" if sys.platform == "win32" else "gedit")
        editor.clicked.connect(editor.launch_application)
        self.taskbar_layout.addWidget(editor)
        self.app_buttons.append(editor)
        
        # Add GitHub Desktop (if available)
        github_desktop = TaskbarButton(QIcon.fromTheme("github", QIcon(":/icons/github.png")), "GitHub", self)
        github_path = "C:\\Users\\AppData\\Local\\GitHubDesktop\\GitHubDesktop.exe" if sys.platform == "win32" else "github-desktop"
        github_desktop.set_application(github_path)
        github_desktop.clicked.connect(github_desktop.launch_application)
        self.taskbar_layout.addWidget(github_desktop)
        self.app_buttons.append(github_desktop)
    
    def add_application_button(self, icon, title, app_path, app_args=None):
        """Add an application button to the taskbar."""
        button = TaskbarButton(icon, title, self)
        button.set_application(app_path, app_args)
        button.clicked.connect(button.launch_application)
        
        # Insert before the stretch
        self.taskbar_layout.insertWidget(self.taskbar_layout.count() - 1, button)
        self.app_buttons.append(button)
        return button
    
    def _load_plugins(self):
        """Load and initialize plugins."""
        try:
            # Get all loaded plugins
            self.plugins = self.plugin_manager.get_all_plugins()
            
            # Initialize plugin UIs
            for name, plugin in self.plugins.items():
                try:
                    if hasattr(plugin, "get_ui"):
                        ui = plugin.get_ui()
                        if ui:
                            self.plugin_uis[name] = ui
                            
                            # Add plugin button to taskbar if it has an icon
                            if hasattr(plugin, "get_icon") and hasattr(plugin, "get_title"):
                                icon = plugin.get_icon()
                                title = plugin.get_title()
                                
                                if icon and title:
                                    button = TaskbarButton(icon, title, self)
                                    button.clicked.connect(lambda checked, p=plugin: self._activate_plugin(p))
                                    self.taskbar_layout.insertWidget(self.taskbar_layout.count() - 1, button)
                                    self.app_buttons.append(button)
                except Exception as e:
                    logger.error(f"Error initializing plugin UI for {name}: {e}", exc_info=True)
            
            logger.info(f"Loaded {len(self.plugins)} plugins")
        except Exception as e:
            logger.error(f"Error loading plugins: {e}", exc_info=True)
    
    def _position_toolbar(self):
        """Position the toolbar at the bottom of the screen."""
        desktop = QDesktopWidget().availableGeometry()
        
        # Set height based on content
        self.setFixedHeight(48)  # Fixed height for taskbar
        
        # Set width to full screen width
        self.setFixedWidth(desktop.width())
        
        # Position at bottom of screen
        self.move(desktop.x(), desktop.height() - self.height())
        
        logger.info(f"Positioned toolbar at {desktop.x()}, {desktop.height() - self.height()} with size {desktop.width()}x{self.height()}")
    
    def _auto_save(self):
        """Auto-save configuration."""
        try:
            self.config.save()
            logger.debug("Configuration auto-saved")
        except Exception as e:
            logger.error(f"Error auto-saving configuration: {e}", exc_info=True)
    
    def _show_settings(self):
        """Show settings dialog."""
        try:
            settings_dialog = ToolbarSettingsDialog(self.config, self)
            settings_dialog.exec_()
            logger.info("Settings dialog shown")
        except Exception as e:
            logger.error(f"Error showing settings dialog: {e}", exc_info=True)
            QMessageBox.critical(self, "Settings Error", f"Error showing settings dialog: {str(e)}")
    
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
