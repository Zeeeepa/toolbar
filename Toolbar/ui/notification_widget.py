#!/usr/bin/env python3
import os
import sys
import logging
from typing import Dict, List, Optional, Any
import time

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QGraphicsOpacityEffect, QFrame, QScrollArea
)
from PyQt5.QtGui import QIcon, QColor, QPalette
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize

logger = logging.getLogger(__name__)

class NotificationWidget(QWidget):
    """
    Notification widget for displaying temporary messages.
    Automatically fades out after a specified duration.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the notification widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.parent = parent
        self.notifications = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize the notification widget UI"""
        # Set window properties
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: #202020;
                border: 1px solid #404040;
                border-radius: 5px;
            }
        """)
        
        # Create content widget
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(5)
        self.content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Set size and style
        self.setFixedSize(300, 400)
        self.setStyleSheet("""
            QWidget {
                background: transparent;
                color: #ffffff;
            }
            QPushButton {
                background: #404040;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #505050;
            }
            QLabel {
                background: #303030;
                padding: 10px;
                border-radius: 3px;
            }
        """)
        
    def add_notification(self, title, message, icon=None, callback=None):
        """Add a new notification"""
        try:
            # Create notification widget
            notif = QWidget()
            notif_layout = QVBoxLayout(notif)
            notif_layout.setContentsMargins(0, 0, 0, 0)
            notif_layout.setSpacing(5)
            
            # Add title
            title_label = QLabel(title)
            title_label.setStyleSheet("font-weight: bold;")
            notif_layout.addWidget(title_label)
            
            # Add message
            msg_label = QLabel(message)
            msg_label.setWordWrap(True)
            notif_layout.addWidget(msg_label)
            
            # Add action button if callback provided
            if callback:
                action_btn = QPushButton("View")
                if icon:
                    action_btn.setIcon(QIcon(icon))
                action_btn.clicked.connect(callback)
                notif_layout.addWidget(action_btn)
            
            # Add to notifications list
            self.notifications.append({
                "widget": notif,
                "time": QTimer()
            })
            
            # Add to layout
            self.content_layout.insertWidget(0, notif)
            
            # Auto-remove after 10 seconds
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.remove_notification(notif))
            timer.start(10000)
            
        except Exception as e:
            if self.parent:
                self.parent.logger.error(f"Error adding notification: {str(e)}")
                self.parent.logger.error(f"{str(e)}", exc_info=True)
            
    def remove_notification(self, notif):
        """Remove a notification"""
        try:
            # Remove from layout
            self.content_layout.removeWidget(notif)
            notif.deleteLater()
            
            # Remove from list
            self.notifications = [n for n in self.notifications if n["widget"] != notif]
            
        except Exception as e:
            if self.parent:
                self.parent.logger.error(f"Error removing notification: {str(e)}")
                self.parent.logger.error(f"{str(e)}", exc_info=True)
                
    def show(self):
        """Show the notification widget"""
        if self.parent:
            # Position next to notification icon
            pos = self.parent.mapToGlobal(self.parent.rect().topRight())
            self.move(pos.x() - self.width(), pos.y() - self.height())
        super().show()
