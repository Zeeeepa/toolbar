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
    QLineEdit, QComboBox, QCheckBox, QGroupBox, QScrollArea, QTextEdit,
    QSystemTrayIcon
)
from PyQt5.QtGui import QIcon, QCursor, QKeySequence, QColor, QPalette, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, QModelIndex, QRect

# Import from Toolbar modules
from Toolbar.ui.toolbar_settings import ToolbarSettingsDialog
from Toolbar.ui.notification_widget import NotificationWidget
from Toolbar.core.plugin_system import PluginType, PluginState, Plugin

logger = logging.getLogger(__name__)

class PluginButton(QToolButton):
    """Custom button for plugins in the toolbar."""
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.setIcon(plugin.get_icon())
        self.setToolTip(f"{plugin.name} v{plugin.version}")
        self.setText(plugin.get_title())
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.clicked.connect(self._on_clicked)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Set fixed size
        self.setIconSize(QSize(32, 32))
        self.setFixedSize(QSize(64, 64))
    
    def _on_clicked(self):
        """Handle button click."""
        try:
            # Call the plugin's activate method
            if hasattr(self.plugin, "activate"):
                self.plugin.activate()
        except Exception as e:
            logger.error(f"Error activating plugin {self.plugin.name}: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Plugin Error",
                f"Error activating plugin {self.plugin.name}: {str(e)}"
            )

class PluginSettingsDialog(QDialog):
    """Dialog for plugin settings."""
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.setWindowTitle(f"{plugin.name} Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Get plugin settings UI
        settings_ui = plugin.get_settings_ui()
        if settings_ui:
            layout.addWidget(settings_ui)
        else:
            # Create a default settings UI
            layout.addWidget(QLabel(f"No settings available for {plugin.name}"))
        
        # Add buttons
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(close_button)

class ToolbarUI(QMainWindow):
    """
    Enhanced toolbar window with plugin management.
    This class provides a robust interface for the toolbar application.
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
        self.plugin_buttons = {}
        self.plugin_menus = {}
        self.tray_icon = None
        
        # Set window properties
        self.setWindowTitle("Toolbar")
        
        # Get position and opacity from config
        self.position = self.config.get_setting("ui.position", "top")
        self.opacity = float(self.config.get_setting("ui.opacity", 0.9))
        self.stay_on_top = self.config.get_setting("ui.stay_on_top", True)
        
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
        
        # Create system tray icon if enabled
        if self.config.get_setting("ui.minimize_to_tray", True):
            self._create_tray_icon()
        
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
            # Create plugin container
            self.plugin_container = QWidget()
            self.plugin_layout = QHBoxLayout(self.plugin_container)
            self.plugin_layout.setContentsMargins(2, 2, 2, 2)
            self.plugin_layout.setSpacing(4)
            
            # Add plugin container to main layout
            self.main_layout.addWidget(self.plugin_container)
            
            # Create settings button
            self.settings_action = QAction(QIcon.fromTheme("preferences-system"), "Settings", self)
            self.settings_action.triggered.connect(self._show_settings)
            self.toolbar.addAction(self.settings_action)
            
            # Create plugin manager button
            self.plugin_manager_action = QAction(QIcon.fromTheme("system-software-install"), "Plugins", self)
            self.plugin_manager_action.triggered.connect(self._show_plugin_manager)
            self.toolbar.addAction(self.plugin_manager_action)
            
            # Create notification area
            self.notification_widget = NotificationWidget(self)
            self.toolbar.addWidget(self.notification_widget)
            
            logger.info("UI components initialized")
        except Exception as e:
            logger.error(f"Error initializing UI components: {e}", exc_info=True)
            raise
    
    def _load_plugins(self):
        """Load and display plugins."""
        try:
            # Clear existing plugin buttons
            for button in self.plugin_buttons.values():
                self.plugin_layout.removeWidget(button)
                button.deleteLater()
            self.plugin_buttons = {}
            
            # Get all plugins
            plugins = self.plugin_manager.get_all_plugins()
            
            # Create buttons for each plugin
            for plugin_id, plugin in plugins.items():
                if plugin.state == PluginState.ACTIVATED:
                    try:
                        # Create button for the plugin
                        button = PluginButton(plugin, self)
                        self.plugin_layout.addWidget(button)
                        self.plugin_buttons[plugin_id] = button
                        
                        logger.info(f"Added button for plugin: {plugin_id}")
                    except Exception as e:
                        logger.error(f"Error creating button for plugin {plugin_id}: {e}", exc_info=True)
            
            # Add spacer to push buttons to the left
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.plugin_layout.addWidget(spacer)
            
            logger.info(f"Loaded {len(self.plugin_buttons)} plugin buttons")
        except Exception as e:
            logger.error(f"Error loading plugins: {e}", exc_info=True)
            raise
    
    def _position_toolbar(self):
        """Position the toolbar on the screen."""
        try:
            # Get screen geometry
            screen = QDesktopWidget().screenGeometry()
            
            # Calculate position based on configuration
            if self.position == "top":
                x = (screen.width() - self.width()) // 2
                y = 0
            elif self.position == "bottom":
                x = (screen.width() - self.width()) // 2
                y = screen.height() - self.height()
            elif self.position == "left":
                x = 0
                y = (screen.height() - self.height()) // 2
            else:  # right
                x = screen.width() - self.width()
                y = (screen.height() - self.height()) // 2
            
            # Move the toolbar
            self.move(x, y)
            
            logger.info(f"Positioned toolbar at ({x}, {y})")
        except Exception as e:
            logger.error(f"Error positioning toolbar: {e}", exc_info=True)
    
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
            new_position = self.config.get_setting("ui.position", "top")
            new_opacity = float(self.config.get_setting("ui.opacity", 0.9))
            new_stay_on_top = self.config.get_setting("ui.stay_on_top", True)
            
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
                
                # Re-add the plugin container
                self.main_layout.addWidget(self.plugin_container)
                
                # Reposition the toolbar
                self._position_toolbar()
            
            # Update tray icon if minimize_to_tray setting changed
            minimize_to_tray = self.config.get_setting("ui.minimize_to_tray", True)
            if minimize_to_tray and not self.tray_icon:
                self._create_tray_icon()
            elif not minimize_to_tray and self.tray_icon:
                self.tray_icon.hide()
                self.tray_icon = None
            
            logger.info(f"Applied settings: position={self.position}, opacity={self.opacity}, stay_on_top={self.stay_on_top}")
        except Exception as e:
            logger.error(f"Error applying settings: {e}", exc_info=True)
            QMessageBox.critical(self, "Settings Error", f"Error applying settings: {str(e)}")
    
    def _show_plugin_manager(self):
        """Show plugin manager dialog."""
        try:
            # Create plugin manager dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Plugin Manager")
            dialog.setMinimumWidth(600)
            dialog.setMinimumHeight(400)
            
            # Create layout
            layout = QVBoxLayout(dialog)
            
            # Create tab widget
            tab_widget = QTabWidget()
            layout.addWidget(tab_widget)
            
            # Create installed plugins tab
            installed_tab = QWidget()
            installed_layout = QVBoxLayout(installed_tab)
            
            # Create plugin list
            plugin_list = QListWidget()
            installed_layout.addWidget(plugin_list)
            
            # Add plugins to list
            plugins = self.plugin_manager.get_all_plugins()
            for plugin_id, plugin in plugins.items():
                item = QListWidgetItem(f"{plugin.name} v{plugin.version}")
                item.setData(Qt.UserRole, plugin_id)
                plugin_list.addItem(item)
            
            # Create plugin details widget
            plugin_details = QTextEdit()
            plugin_details.setReadOnly(True)
            installed_layout.addWidget(plugin_details)
            
            # Connect plugin list selection to show details
            plugin_list.currentItemChanged.connect(
                lambda current, previous: self._show_plugin_details(current, plugin_details)
            )
            
            # Add buttons
            buttons_layout = QHBoxLayout()
            installed_layout.addLayout(buttons_layout)
            
            # Add enable/disable button
            enable_disable_button = QPushButton("Enable/Disable")
            enable_disable_button.clicked.connect(
                lambda: self._toggle_plugin_state(plugin_list.currentItem())
            )
            buttons_layout.addWidget(enable_disable_button)
            
            # Add settings button
            settings_button = QPushButton("Settings")
            settings_button.clicked.connect(
                lambda: self._show_plugin_settings(plugin_list.currentItem())
            )
            buttons_layout.addWidget(settings_button)
            
            # Add reload button
            reload_button = QPushButton("Reload")
            reload_button.clicked.connect(
                lambda: self._reload_plugin(plugin_list.currentItem())
            )
            buttons_layout.addWidget(reload_button)
            
            # Add installed tab to tab widget
            tab_widget.addTab(installed_tab, "Installed Plugins")
            
            # Create failed plugins tab
            failed_tab = QWidget()
            failed_layout = QVBoxLayout(failed_tab)
            
            # Create failed plugin list
            failed_list = QListWidget()
            failed_layout.addWidget(failed_list)
            
            # Add failed plugins to list
            failed_plugins = self.plugin_manager.get_failed_plugins()
            for plugin_id, error in failed_plugins.items():
                item = QListWidgetItem(f"{plugin_id} (Failed)")
                item.setData(Qt.UserRole, plugin_id)
                item.setData(Qt.UserRole + 1, error)
                failed_list.addItem(item)
            
            # Create failed plugin details widget
            failed_details = QTextEdit()
            failed_details.setReadOnly(True)
            failed_layout.addWidget(failed_details)
            
            # Connect failed plugin list selection to show details
            failed_list.currentItemChanged.connect(
                lambda current, previous: self._show_failed_plugin_details(current, failed_details)
            )
            
            # Add buttons
            failed_buttons_layout = QHBoxLayout()
            failed_layout.addLayout(failed_buttons_layout)
            
            # Add disable button
            disable_button = QPushButton("Disable")
            disable_button.clicked.connect(
                lambda: self._disable_failed_plugin(failed_list.currentItem())
            )
            failed_buttons_layout.addWidget(disable_button)
            
            # Add failed tab to tab widget
            tab_widget.addTab(failed_tab, "Failed Plugins")
            
            # Add close button
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            # Show dialog
            dialog.exec_()
            
            # Reload plugins after dialog is closed
            self._load_plugins()
            
            logger.info("Plugin manager dialog shown")
        except Exception as e:
            logger.error(f"Error showing plugin manager dialog: {e}", exc_info=True)
            QMessageBox.critical(self, "Plugin Manager Error", f"Error showing plugin manager dialog: {str(e)}")
    
    def _show_plugin_details(self, item, details_widget):
        """Show details for a plugin."""
        if not item:
            details_widget.clear()
            return
        
        try:
            plugin_id = item.data(Qt.UserRole)
            plugin = self.plugin_manager.get_plugin(plugin_id)
            
            if plugin:
                # Update plugin details
                details_widget.setHtml(f"""
                    <h2>{plugin.name} v{plugin.version}</h2>
                    <p><b>Description:</b> {plugin.description}</p>
                    <p><b>Status:</b> {plugin.state.value}</p>
                    <p><b>Type:</b> {plugin.manifest.plugin_type.value if plugin.manifest else "Unknown"}</p>
                    <p><b>Author:</b> {plugin.manifest.author if plugin.manifest else "Unknown"}</p>
                """)
                
                logger.info(f"Plugin details shown for {plugin_id}")
        except Exception as e:
            logger.error(f"Error showing plugin details: {e}", exc_info=True)
            details_widget.setHtml(f"<p>Error showing plugin details: {str(e)}</p>")
    
    def _show_failed_plugin_details(self, item, details_widget):
        """Show details for a failed plugin."""
        if not item:
            details_widget.clear()
            return
        
        try:
            plugin_id = item.data(Qt.UserRole)
            error = item.data(Qt.UserRole + 1)
            
            # Update plugin details
            details_widget.setHtml(f"""
                <h2>{plugin_id}</h2>
                <p><b>Status:</b> Failed</p>
                <p><b>Error:</b> {error}</p>
            """)
            
            logger.info(f"Failed plugin details shown for {plugin_id}")
        except Exception as e:
            logger.error(f"Error showing failed plugin details: {e}", exc_info=True)
            details_widget.setHtml(f"<p>Error showing failed plugin details: {str(e)}</p>")
    
    def _toggle_plugin_state(self, item):
        """Toggle the state of a plugin."""
        if not item:
            return
        
        try:
            plugin_id = item.data(Qt.UserRole)
            plugin = self.plugin_manager.get_plugin(plugin_id)
            
            if plugin:
                if plugin.state == PluginState.ACTIVATED:
                    # Deactivate the plugin
                    plugin.deactivate()
                    QMessageBox.information(self, "Plugin Deactivated", f"Plugin {plugin.name} has been deactivated.")
                    logger.info(f"Plugin {plugin_id} deactivated")
                else:
                    # Activate the plugin
                    plugin.activate()
                    QMessageBox.information(self, "Plugin Activated", f"Plugin {plugin.name} has been activated.")
                    logger.info(f"Plugin {plugin_id} activated")
                
                # Update the item text
                item.setText(f"{plugin.name} v{plugin.version}")
        except Exception as e:
            logger.error(f"Error toggling plugin state: {e}", exc_info=True)
            QMessageBox.critical(self, "Plugin Error", f"Error toggling plugin state: {str(e)}")
    
    def _show_plugin_settings(self, item):
        """Show settings for a plugin."""
        if not item:
            return
        
        try:
            plugin_id = item.data(Qt.UserRole)
            plugin = self.plugin_manager.get_plugin(plugin_id)
            
            if plugin:
                # Show plugin settings dialog
                dialog = PluginSettingsDialog(plugin, self)
                dialog.exec_()
                logger.info(f"Plugin settings shown for {plugin_id}")
        except Exception as e:
            logger.error(f"Error showing plugin settings: {e}", exc_info=True)
            QMessageBox.critical(self, "Plugin Settings Error", f"Error showing plugin settings: {str(e)}")
    
    def _reload_plugin(self, item):
        """Reload a plugin."""
        if not item:
            return
        
        try:
            plugin_id = item.data(Qt.UserRole)
            
            # Reload the plugin
            success = self.plugin_manager.reload_plugin(plugin_id)
            
            if success:
                QMessageBox.information(self, "Plugin Reloaded", f"Plugin {plugin_id} has been reloaded.")
                logger.info(f"Plugin {plugin_id} reloaded")
                
                # Update the item text
                plugin = self.plugin_manager.get_plugin(plugin_id)
                if plugin:
                    item.setText(f"{plugin.name} v{plugin.version}")
            else:
                QMessageBox.warning(self, "Plugin Reload Failed", f"Failed to reload plugin {plugin_id}.")
                logger.warning(f"Failed to reload plugin {plugin_id}")
        except Exception as e:
            logger.error(f"Error reloading plugin: {e}", exc_info=True)
            QMessageBox.critical(self, "Plugin Reload Error", f"Error reloading plugin: {str(e)}")
    
    def _disable_failed_plugin(self, item):
        """Disable a failed plugin."""
        if not item:
            return
        
        try:
            plugin_id = item.data(Qt.UserRole)
            
            # Disable the plugin
            self.plugin_manager.disable_plugin(plugin_id)
            
            QMessageBox.information(self, "Plugin Disabled", f"Plugin {plugin_id} has been disabled.")
            logger.info(f"Failed plugin {plugin_id} disabled")
            
            # Remove the item from the list
            item.listWidget().takeItem(item.listWidget().row(item))
        except Exception as e:
            logger.error(f"Error disabling failed plugin: {e}", exc_info=True)
            QMessageBox.critical(self, "Plugin Disable Error", f"Error disabling failed plugin: {str(e)}")
    
    def _create_tray_icon(self):
        """Create system tray icon."""
        try:
            # Create tray icon
            self.tray_icon = QSystemTrayIcon(QIcon.fromTheme("applications-system"), self)
            
            # Create tray menu
            tray_menu = QMenu()
            
            # Add show/hide action
            show_hide_action = QAction("Show/Hide Toolbar", self)
            show_hide_action.triggered.connect(self._toggle_visibility)
            tray_menu.addAction(show_hide_action)
            
            # Add settings action
            settings_action = QAction("Settings", self)
            settings_action.triggered.connect(self._show_settings)
            tray_menu.addAction(settings_action)
            
            # Add plugin manager action
            plugin_manager_action = QAction("Plugins", self)
            plugin_manager_action.triggered.connect(self._show_plugin_manager)
            tray_menu.addAction(plugin_manager_action)
            
            # Add separator
            tray_menu.addSeparator()
            
            # Add exit action
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self.close)
            tray_menu.addAction(exit_action)
            
            # Set tray menu
            self.tray_icon.setContextMenu(tray_menu)
            
            # Connect tray icon activated signal
            self.tray_icon.activated.connect(self._tray_icon_activated)
            
            # Show tray icon
            self.tray_icon.show()
            
            logger.info("System tray icon created")
        except Exception as e:
            logger.error(f"Error creating system tray icon: {e}", exc_info=True)
    
    def _toggle_visibility(self):
        """Toggle toolbar visibility."""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def _tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.Trigger:
            self._toggle_visibility()
    
    def closeEvent(self, event):
        """Handle close event."""
        try:
            # Check if minimize to tray is enabled
            if self.config.get_setting("ui.minimize_to_tray", True) and self.tray_icon:
                # Minimize to tray instead of closing
                self.hide()
                event.ignore()
                return
            
            # Save configuration
            self.config.save()
            
            # Clean up plugins
            self.plugin_manager.cleanup()
            
            logger.info("Toolbar closed")
            event.accept()
        except Exception as e:
            logger.error(f"Error during close event: {e}", exc_info=True)
            event.accept()
