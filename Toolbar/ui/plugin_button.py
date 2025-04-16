import logging
from PyQt5.QtWidgets import QPushButton, QMenu, QAction
from PyQt5.QtGui import QIcon

logger = logging.getLogger(__name__)

class PluginButton(QPushButton):
    """Button for plugin actions"""
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.init_ui()

    def init_ui(self):
        """Initialize button UI"""
        try:
            # Set button properties
            self.setIcon(QIcon(self.plugin.get_icon()))
            self.setToolTip(self.plugin.name)
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    padding: 5px;
                    min-width: 30px;
                    min-height: 30px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.1);
                }
            """)

            # Create context menu
            menu = QMenu(self)
            for action in self.plugin.get_actions():
                menu_action = QAction(action["name"], self)
                menu_action.triggered.connect(action["callback"])
                menu.addAction(menu_action)

            self.setMenu(menu)
            self.clicked.connect(self.handle_click)

        except Exception as e:
            logger.error("Error initializing plugin button for %s: %s", self.plugin.name, str(e))
            logger.error(str(e), exc_info=True)

    def handle_click(self):
        """Handle button click"""
        try:
            if self.plugin.is_active():
                self.showMenu()
        except Exception as e:
            logger.error("Error handling click for %s: %s", self.plugin.name, str(e))
            logger.error(str(e), exc_info=True)
