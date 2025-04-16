import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class PluginManagerDialog(QDialog):
    """Dialog for managing plugins"""
    def __init__(self, plugin_manager):
        super().__init__()
        self.plugin_manager = plugin_manager
        self.init_ui()

    def init_ui(self):
        """Initialize dialog UI"""
        try:
            self.setWindowTitle("Plugin Manager")
            layout = QVBoxLayout()

            # Add plugin list
            self.plugin_list = QListWidget()
            self.load_plugins()
            layout.addWidget(self.plugin_list)

            # Add buttons
            button_layout = QHBoxLayout()
            refresh_button = QPushButton("Refresh")
            refresh_button.clicked.connect(self.refresh_plugins)
            close_button = QPushButton("Close")
            close_button.clicked.connect(self.accept)
            button_layout.addWidget(refresh_button)
            button_layout.addWidget(close_button)
            layout.addLayout(button_layout)

            self.setLayout(layout)

        except Exception as e:
            logger.error("Error initializing plugin manager dialog: %s", str(e))
            logger.error(str(e), exc_info=True)

    def load_plugins(self):
        """Load plugins into list widget"""
        try:
            self.plugin_list.clear()
            for plugin in self.plugin_manager.get_all_plugins():
                item = QListWidgetItem()
                item.setText(f"{plugin.name} v{plugin.version}")
                item.setToolTip(plugin.description)
                if plugin.is_active():
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
                self.plugin_list.addItem(item)

        except Exception as e:
            logger.error("Error loading plugins: %s", str(e))
            logger.error(str(e), exc_info=True)

    def refresh_plugins(self):
        """Refresh plugin list"""
        try:
            self.plugin_manager.load_plugins()
            self.load_plugins()
        except Exception as e:
            logger.error("Error refreshing plugins: %s", str(e))
            logger.error(str(e), exc_info=True)
