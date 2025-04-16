from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QMenu, QAction, QSystemTrayIcon
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QIcon, QScreen
from .notification_widget import NotificationWidget
from .plugin_button import PluginButton
from .toolbar_settings import SettingsDialog
from .plugin_manager import PluginManagerDialog

logger = logging.getLogger(__name__)

class ToolbarUI(QMainWindow):
    def __init__(self, config=None, plugin_manager=None):
        super().__init__()
        self.config = config
        self.plugin_manager = plugin_manager
        self.notification_widget = NotificationWidget()
        self.init_ui()

    def init_ui(self):
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left section for system icons
        left_section = QWidget()
        left_layout = QHBoxLayout(left_section)
        left_layout.setContentsMargins(5, 0, 5, 0)
        left_layout.setSpacing(2)

        # Settings button
        settings_btn = QPushButton()
        settings_btn.setIcon(QIcon("Toolbar/assets/settings.png"))
        settings_btn.clicked.connect(self.show_settings)
        settings_btn.setFixedSize(32, 32)
        left_layout.addWidget(settings_btn)

        # GitHub button
        github_btn = QPushButton()
        github_btn.setIcon(QIcon("Toolbar/assets/github.png"))
        github_btn.clicked.connect(self.show_github_manager)
        github_btn.setFixedSize(32, 32)
        left_layout.addWidget(github_btn)

        layout.addWidget(left_section)

        # Middle section for repository shortcuts
        middle_section = QWidget()
        middle_layout = QHBoxLayout(middle_section)
        middle_layout.setContentsMargins(5, 0, 5, 0)
        middle_layout.setSpacing(2)
        self._load_plugins(middle_layout)
        layout.addWidget(middle_section, 1)  # Stretch factor 1

        # Right section for notifications
        right_section = QWidget()
        right_layout = QHBoxLayout(right_section)
        right_layout.setContentsMargins(5, 0, 5, 0)
        right_layout.setSpacing(2)
        
        # Notification icon
        notif_btn = QPushButton()
        notif_btn.setIcon(QIcon("Toolbar/assets/notification.png"))
        notif_btn.clicked.connect(self.show_notifications)
        notif_btn.setFixedSize(32, 32)
        right_layout.addWidget(notif_btn)
        
        layout.addWidget(right_section)

        # Set window properties
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QMainWindow {
                background: #202020;
                border: none;
            }
            QPushButton {
                background: transparent;
                border: none;
                padding: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
        """)

        # Position at bottom of screen
        self._position_toolbar()
        
        # Create system tray
        self._create_tray()

    def _load_plugins(self, layout):
        """Load plugin buttons into the middle section"""
        if not self.plugin_manager:
            return
            
        for plugin in self.plugin_manager.get_active_plugins():
            try:
                if not plugin.is_active():
                    continue
                    
                button = PluginButton(plugin, self)
                layout.addWidget(button)
                self.logger.info(f"Added button for plugin: {plugin.name}")
            except Exception as e:
                self.logger.error(f"Error creating button for plugin {plugin.name}: {str(e)}")
                self.logger.error(f"{str(e)}", exc_info=True)

    def _position_toolbar(self):
        """Position toolbar at bottom of screen"""
        screen = QScreen.virtualGeometry(QApplication.primaryScreen())
        toolbar_height = 40
        self.setGeometry(0, screen.height() - toolbar_height, screen.width(), toolbar_height)

    def _create_tray(self):
        """Create system tray icon"""
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon("Toolbar/assets/tray.png"))
        self.tray.setVisible(True)
        
        # Tray menu
        tray_menu = QMenu()
        settings_action = tray_menu.addAction("Settings")
        settings_action.triggered.connect(self.show_settings)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.close)
        self.tray.setContextMenu(tray_menu)

    def show_settings(self):
        """Show settings dialog"""
        try:
            settings_dialog = SettingsDialog(self.config)
            settings_dialog.exec_()
        except Exception as e:
            self.logger.error(f"Error showing settings: {str(e)}")
            self.logger.error(f"{str(e)}", exc_info=True)

    def show_github_manager(self):
        """Show GitHub repository manager"""
        try:
            github_plugin = self.plugin_manager.get_plugin("github")
            if github_plugin:
                github_plugin.show_manager()
        except Exception as e:
            self.logger.error(f"Error showing GitHub manager: {str(e)}")
            self.logger.error(f"{str(e)}", exc_info=True)

    def show_notifications(self):
        """Show notifications panel"""
        try:
            self.notification_widget.show()
        except Exception as e:
            self.logger.error(f"Error showing notifications: {str(e)}")
            self.logger.error(f"{str(e)}", exc_info=True)
