from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QLabel, QMessageBox)
from PyQt5.QtCore import Qt

class PluginManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Plugin Manager")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Plugin list
        self.plugin_list = QListWidget()
        self.refresh_plugin_list()
        layout.addWidget(self.plugin_list)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_plugin_list)
        button_layout.addWidget(self.refresh_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def refresh_plugin_list(self):
        """Refresh the list of plugins"""
        self.plugin_list.clear()
        if not hasattr(self.parent, 'plugin_manager'):
            return

        for plugin in self.parent.plugin_manager.get_plugins():
            status = "Active" if plugin.is_active() else "Inactive"
            self.plugin_list.addItem(f"{plugin.name} - {status}")

    def show_error(self, message):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)
