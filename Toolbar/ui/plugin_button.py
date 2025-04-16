from typing import Any, Dict, List, Optional
import logging
from PyQt5.QtWidgets import QPushButton, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class PluginButton(QPushButton):
    """Button for plugin actions in the toolbar."""

    def __init__(self, plugin: Any, parent: Any = None):
        super().__init__(parent)
        self.plugin = plugin
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the button UI."""
        try:
            # Set button properties
            self.setText(self.plugin.name)
            if self.plugin.icon:
                self.setIcon(QIcon(self.plugin.icon))

            # Create context menu
            menu = QMenu(self)
            for action in self.plugin.get_actions():
                try:
                    menu_action = QAction(action["name"], self)
                    menu_action.triggered.connect(action["callback"])
                    menu.addAction(menu_action)
                except Exception as e:
                    logger.error(f"Error adding action {action}: {str(e)}")
                    logger.error(str(e), exc_info=True)

            # Set button style
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    padding: 5px;
                    min-width: 30px;
                    min-height: 30px;
                    color: white;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.1);
                }
            """)

            # Set context menu
            self.setMenu(menu)

        except Exception as e:
            logger.error(f"Error initializing plugin button for {self.plugin.name}: {str(e)}")
            logger.error(str(e), exc_info=True)

    def mousePressEvent(self, event: Any) -> None:
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            # Show context menu on left click
            if self.menu():
                self.showMenu()
        else:
            super().mousePressEvent(event)
