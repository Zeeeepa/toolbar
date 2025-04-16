from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QDesktopWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon

from .plugin_button import PluginButton
from .toolbar_settings import SettingsDialog
from .plugin_manager import PluginManagerDialog

class ToolbarUI(QMainWindow):
    def __init__(self, config=None, plugin_manager=None):
        super().__init__()
        self.config = config
        self.plugin_manager = plugin_manager
        self.settings_dialog = None
        self.plugin_manager_dialog = None
        self.init_ui()

    def init_ui(self):
        # Set window flags for taskbar-like behavior
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add plugin buttons
        if self.plugin_manager:
            self._load_plugins()

        # Position toolbar at bottom of screen
        self.position_toolbar()

        # Set window title and show
        self.setWindowTitle('Toolbar')
        self.show()

    def _load_plugins(self):
        """Load plugin buttons"""
        for plugin in self.plugin_manager.get_active_plugins():
            try:
                button = PluginButton(plugin, self)
                self.centralWidget().layout().addWidget(button)
            except Exception as e:
                print(f"Error creating button for plugin {plugin.name}: {str(e)}")

    def position_toolbar(self):
        """Position toolbar at bottom of screen with full width"""
        screen = QDesktopWidget().screenGeometry()
        toolbar_height = 40
        self.setGeometry(0, screen.height() - toolbar_height, screen.width(), toolbar_height)

    def show_settings(self):
        """Show settings dialog"""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self.config, self)
        self.settings_dialog.show()

    def show_plugin_manager(self):
        """Show plugin manager dialog"""
        if not self.plugin_manager_dialog:
            self.plugin_manager_dialog = PluginManagerDialog(self.plugin_manager, self)
        self.plugin_manager_dialog.show()
