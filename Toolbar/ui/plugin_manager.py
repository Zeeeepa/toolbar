import logging
from typing import Any, Dict, List, Optional
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QWidget, QCheckBox
)

logger = logging.getLogger(__name__)

class PluginManagerDialog(QDialog):
    """Dialog for managing plugins."""

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.parent = parent
        self.plugin_manager = parent.plugin_manager if parent else None
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the dialog UI."""
        try:
            self.setWindowTitle("Plugin Manager")
            layout = QVBoxLayout()

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
            self.setLayout(layout)

        except Exception as e:
            logger.error("Error initializing plugin manager dialog: %s", str(e))
            logger.error(str(e), exc_info=True)

    def _load_plugins(self) -> None:
        """Load and display plugins."""
        try:
            self.plugin_list.clear()
            if not self.plugin_manager:
                return

            for plugin in self.plugin_manager.get_all_plugins():
                try:
                    # Create list item widget
                    item = QListWidgetItem()
                    self.plugin_list.addItem(item)

                    # Create widget for plugin info
                    widget = QWidget()
                    layout = QHBoxLayout(widget)

                    # Add plugin name and version
                    name_label = QLabel(f"{plugin.name} v{plugin.version}")
                    layout.addWidget(name_label)

                    # Add description
                    if plugin.description:
                        desc_label = QLabel(plugin.description)
                        desc_label.setStyleSheet("color: gray;")
                        layout.addWidget(desc_label)

                    # Add spacer
                    layout.addStretch()

                    # Add active checkbox
                    active_check = QCheckBox("Active")
                    active_check.setChecked(plugin.is_active)
                    active_check.stateChanged.connect(
                        lambda state, p=plugin: self._toggle_plugin(p, state)
                    )
                    layout.addWidget(active_check)

                    # Set widget for item
                    item.setSizeHint(widget.sizeHint())
                    self.plugin_list.setItemWidget(item, widget)

                except Exception as e:
                    logger.error("Error adding plugin %s: %s", plugin.name, str(e))
                    logger.error(str(e), exc_info=True)

        except Exception as e:
            logger.error("Error loading plugins: %s", str(e))
            logger.error(str(e), exc_info=True)

    def _toggle_plugin(self, plugin: Any, state: int) -> None:
        """Toggle a plugin's active state."""
        try:
            if state == Qt.Checked:
                plugin.initialize(self.plugin_manager.config,
                                self.plugin_manager.event_bus,
                                self.plugin_manager.toolbar)
            else:
                plugin._active = False

            # Update parent toolbar
            if self.parent:
                self.parent.init_ui()

        except Exception as e:
            logger.error("Error toggling plugin %s: %s", plugin.name, str(e))
            logger.error(str(e), exc_info=True)
