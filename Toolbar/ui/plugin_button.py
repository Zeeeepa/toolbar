import logging
import os
from typing import Any, Dict, List, Optional
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QPushButton, QMenu, QAction

logger = logging.getLogger(__name__)

class PluginButton(QPushButton):
    """Button for plugin actions."""

    def __init__(self, plugin: Any, parent: Any = None) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the button UI."""
        try:
            # Set button properties
            self.setToolTip(self.plugin.description)
            
            # Set icon if available
            if self.plugin.icon:
                icon_path = os.path.join("icons", self.plugin.icon)
                if os.path.exists(icon_path):
                    self.setIcon(QIcon(icon_path))
                else:
                    logger.warning("Icon not found: %s", icon_path)

            # Create context menu
            menu = QMenu(self)
            actions = self.plugin.get_actions()
            if actions:
                for action in actions:
                    menu_action = QAction(action["name"], self)
                    menu_action.triggered.connect(
                        lambda checked, a=action: self._execute_action(a)
                    )
                    menu.addAction(menu_action)
            else:
                # Add default action if no actions defined
                default_action = QAction(self.plugin.name, self)
                default_action.triggered.connect(self._execute_default_action)
                menu.addAction(default_action)

            self.setMenu(menu)

        except Exception as e:
            logger.error("Error initializing plugin button for %s: %s", 
                        self.plugin.name, str(e))
            logger.error(str(e), exc_info=True)

    def _execute_action(self, action: Dict[str, Any]) -> None:
        """Execute a plugin action."""
        try:
            self.plugin.execute_action(action["id"], action.get("params", {}))
        except Exception as e:
            logger.error("Error executing action %s: %s", action["id"], str(e))
            logger.error(str(e), exc_info=True)

    def _execute_default_action(self) -> None:
        """Execute the default plugin action."""
        try:
            self.plugin.execute_action("default", {})
