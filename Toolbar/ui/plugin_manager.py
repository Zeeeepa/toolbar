from typing import Any, Dict, List, Optional
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class PluginManagerDialog(QDialog):
    """Dialog for managing toolbar plugins."""

    def __init__(self, plugin_manager: Any):
        super().__init__()
        self.plugin_manager = plugin_manager
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the plugin manager dialog UI."""
        try:
            # Set dialog properties
            self.setWindowTitle("Plugin Manager")
            self.setMinimumWidth(400)

            # Create layout
            layout = QVBoxLayout()
            self.setLayout(layout)

            # Add plugin list
            self.plugin_list = QListWidget()
            self._load_plugins()
            layout.addWidget(self.plugin_list)

            # Add buttons
            button_layout = QHBoxLayout()
            refresh_button = QPushButton("Refresh")
            refresh_button.clicked.connect(self._load_plugins)
            button_layout.addWidget(refresh_button)

            close_button = QPushButton("Close")
            close_button.clicked.connect(self.accept)
            button_layout.addWidget(close_button)

            layout.addLayout(button_layout)

        except Exception as e:
            logger.error(f"Error initializing plugin manager dialog: {str(e)}")
            logger.error(str(e), exc_info=True)

    def _load_plugins(self) -> None:
        """Load and display available plugins."""
        try:
            self.plugin_list.clear()
            for plugin in self.plugin_manager.get_all_plugins():
                try:
                    item = QListWidgetItem()
                    item.setText(f"{plugin.name} v{plugin.version}")
                    item.setToolTip(plugin.description)
                    if plugin.is_active():
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
                    self.plugin_list.addItem(item)
                except Exception as e:
                    logger.error(f"Error adding plugin {plugin.name} to list: {str(e)}")
                    logger.error(str(e), exc_info=True)
        except Exception as e:
            logger.error(f"Error loading plugins: {str(e)}")
            logger.error(str(e), exc_info=True)
