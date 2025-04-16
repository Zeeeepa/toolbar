from PyQt5.QtWidgets import QPushButton, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

class PluginButton(QPushButton):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.init_ui()

    def init_ui(self):
        """Initialize the button UI"""
        try:
            # Set button text and icon
            self.setText(self.plugin.name)
            icon = self.plugin.get_icon()
            if isinstance(icon, str):
                self.setIcon(QIcon(icon))
            elif isinstance(icon, QIcon):
                self.setIcon(icon)

            # Create context menu
            self.context_menu = QMenu(self)
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)

            # Add plugin actions to context menu
            for action in self.plugin.get_actions():
                menu_action = QAction(action.name, self)
                menu_action.triggered.connect(action.callback)
                self.context_menu.addAction(menu_action)

            # Connect click handler
            self.clicked.connect(self.handle_click)

        except Exception as e:
            logger.error(f"Error initializing plugin button for {self.plugin.name}: {str(e)}")
            logger.exception(e)

    def handle_click(self):
        """Handle button click event"""
        try:
            self.plugin.handle_click()
        except Exception as e:
            logger.error(f"Error handling click for plugin {self.plugin.name}: {str(e)}")
            logger.exception(e)

    def show_context_menu(self, position):
        """Show the context menu at the given position"""
        try:
            self.context_menu.exec_(self.mapToGlobal(position))
        except Exception as e:
            logger.error(f"Error showing context menu for plugin {self.plugin.name}: {str(e)}")
            logger.exception(e)
