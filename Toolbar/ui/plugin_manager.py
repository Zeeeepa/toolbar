import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QListWidget, QListWidgetItem, QCheckBox)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class PluginManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.plugin_manager = parent.plugin_manager if parent else None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Plugin Manager')
        layout = QVBoxLayout()

        # Plugin list
        self.plugin_list = QListWidget()
        self.load_plugins()
        layout.addWidget(self.plugin_list)

        # Buttons
        button_layout = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_plugins)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_plugins(self):
        self.plugin_list.clear()
        if not self.plugin_manager:
            return

        try:
            for plugin in self.plugin_manager.get_all_plugins():
                item = QListWidgetItem()
                widget = QWidget()
                layout = QHBoxLayout()
                layout.setContentsMargins(5, 2, 5, 2)

                # Plugin name and version
                name_label = QLabel(f"{plugin.name} v{plugin.version}")
                layout.addWidget(name_label)

                # Status
                status_label = QLabel("Active" if plugin.is_active() else "Inactive")
                layout.addWidget(status_label)

                # Enable/disable checkbox
                enable_checkbox = QCheckBox()
                enable_checkbox.setChecked(plugin.is_active())
                enable_checkbox.stateChanged.connect(lambda state, p=plugin: self.toggle_plugin(p, state))
                layout.addWidget(enable_checkbox)

                widget.setLayout(layout)
                item.setSizeHint(widget.sizeHint())
                self.plugin_list.addItem(item)
                self.plugin_list.setItemWidget(item, widget)

        except Exception as e:
            logger.error(f"Error loading plugins: {str(e)}")
            logger.error(str(e), exc_info=True)

    def toggle_plugin(self, plugin, state):
        try:
            if state == Qt.Checked:
                plugin.activate()
            else:
                plugin.deactivate()
            self.refresh_plugins()
        except Exception as e:
            logger.error(f"Error toggling plugin {plugin.name}: {str(e)}")
            logger.error(str(e), exc_info=True)

    def refresh_plugins(self):
        try:
            if self.plugin_manager:
                self.plugin_manager.reload_plugins()
            self.load_plugins()
            if self.parent:
                self.parent._load_plugins()
        except Exception as e:
            logger.error(f"Error refreshing plugins: {str(e)}")
            logger.error(str(e), exc_info=True)
