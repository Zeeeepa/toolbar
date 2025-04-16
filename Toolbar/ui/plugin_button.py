import logging
from PyQt5.QtWidgets import QPushButton, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class PluginButton(QPushButton):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.init_ui()

    def init_ui(self):
        try:
            # Set button text and icon
            self.setText(self.plugin.name)
            icon = self.plugin.get_icon()
            if icon:
                if isinstance(icon, str):
                    self.setIcon(QIcon(icon))
                else:
                    self.setIcon(icon)

            # Create context menu
            self.menu = QMenu(self)
            for action in self.plugin.get_actions():
                menu_action = QAction(action["name"], self)
                menu_action.triggered.connect(action["callback"])
                if "icon" in action:
                    menu_action.setIcon(QIcon(action["icon"]))
                self.menu.addAction(menu_action)

            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_context_menu)

            # Set button style
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    padding: 5px;
                    min-width: 30px;
                    min-height: 30px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.2);
                }
            """)

            # Connect click handler
            self.clicked.connect(self.handle_click)

        except Exception as e:
            logger.error(f"Error initializing plugin button for {self.plugin.name}: {str(e)}")
            logger.error(str(e), exc_info=True)

    def handle_click(self):
        try:
            self.plugin.handle_click()
        except Exception as e:
            logger.error(f"Error handling click for {self.plugin.name}: {str(e)}")
            logger.error(str(e), exc_info=True)

    def show_context_menu(self, pos):
        try:
            self.menu.exec_(self.mapToGlobal(pos))
        except Exception as e:
            logger.error(f"Error showing context menu for {self.plugin.name}: {str(e)}")
            logger.error(str(e), exc_info=True)
