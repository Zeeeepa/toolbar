import warnings
import webbrowser
from PyQt5.QtWidgets import QLabel, QMenu
from PyQt5.QtCore import Qt

# Suppress PyQt5 deprecation warnings
warnings.filterwarnings("ignore", message=".*sipPyTypeDict.*")

class NotificationWidget(QLabel):
    """
    Widget for displaying GitHub notifications.
    """
    def __init__(self, notification, parent=None):
        """
        Initialize a notification widget.
        
        Args:
            notification (GitHubNotification): The notification to display
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.notification = notification
        
        # Set base style
        self.setStyleSheet("background-color: rgba(40, 40, 40, 200); color: white; border-radius: 5px; padding: 5px;")
        self.setText(notification.title)
        self.setToolTip(notification.title)
        self.setFixedWidth(200)
        self.setFixedHeight(30)
        self.setCursor(Qt.PointingHandCursor)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set style based on notification type
        if notification.type == "pr":
            self.setStyleSheet("background-color: rgba(40, 120, 40, 200); color: white; border-radius: 5px; padding: 5px;")
        else:  # branch
            self.setStyleSheet("background-color: rgba(40, 40, 120, 200); color: white; border-radius: 5px; padding: 5px;")
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            webbrowser.open(self.notification.url)
            event.accept()
    
    def show_context_menu(self, position):
        """Show the context menu for this notification."""
        context_menu = QMenu(self)
        
        # Open action
        open_action = context_menu.addAction("Open in Browser")
        open_action.triggered.connect(lambda: webbrowser.open(self.notification.url))
        
        # Remove action
        remove_action = context_menu.addAction("Remove Notification")
        remove_action.triggered.connect(lambda: self.parent().remove_notification(self))
        
        context_menu.exec_(self.mapToGlobal(position))
