#!/usr/bin/env python3
import os
import sys
import logging
from typing import Dict, List, Optional, Any
import time

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QGraphicsOpacityEffect, QFrame
)
from PyQt5.QtGui import QIcon, QColor, QPalette
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize

logger = logging.getLogger(__name__)

class NotificationWidget(QFrame):
    """
    Notification widget for displaying temporary messages.
    Automatically fades out after a specified duration.
    """
    
    def __init__(self, parent=None, duration=5000):
        """
        Initialize the notification widget.
        
        Args:
            parent: Parent widget
            duration: Duration in milliseconds before the notification fades out
        """
        super().__init__(parent)
        self.duration = duration
        
        # Set frame properties
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(1)
        
        # Set widget properties
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                color: #ffffff;
                border-radius: 5px;
                border: 1px solid #3a3a3a;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: transparent;
                color: #ffffff;
                border: none;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-radius: 2px;
            }
        """)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)
        
        # Create header layout
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(5)
        
        # Create title label
        self.title_label = QLabel("Notification")
        self.title_label.setStyleSheet("font-weight: bold;")
        self.header_layout.addWidget(self.title_label)
        
        # Add spacer
        self.header_layout.addStretch()
        
        # Create close button
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(16, 16)
        self.close_button.clicked.connect(self.close)
        self.header_layout.addWidget(self.close_button)
        
        # Add header layout to main layout
        self.layout.addLayout(self.header_layout)
        
        # Create message label
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setTextFormat(Qt.RichText)
        self.layout.addWidget(self.message_label)
        
        # Create opacity effect
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self.opacity_effect)
        
        # Create fade out animation
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutQuad)
        self.fade_animation.finished.connect(self.close)
        
        # Create timer for auto-close
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out)
        
        logger.info("Notification widget initialized")
    
    def show_notification(self, message, title="Notification", duration=None):
        """
        Show a notification with the specified message and title.
        
        Args:
            message: Message to display
            title: Title of the notification
            duration: Duration in milliseconds before the notification fades out
        """
        try:
            # Set title and message
            self.title_label.setText(title)
            self.message_label.setText(message)
            
            # Adjust size
            self.adjustSize()
            
            # Position the notification
            self._position_notification()
            
            # Show the notification
            self.show()
            self.raise_()
            
            # Start the timer
            if duration is None:
                duration = self.duration
            self.timer.start(duration)
            
            logger.info(f"Notification shown: {title} - {message}")
        except Exception as e:
            logger.error(f"Error showing notification: {e}", exc_info=True)
    
    def _position_notification(self):
        """Position the notification in the bottom right corner of the screen."""
        try:
            # Get screen geometry
            screen = self.parent().screen() if self.parent() else self.screen()
            screen_geometry = screen.availableGeometry()
            
            # Calculate position
            x = screen_geometry.width() - self.width() - 20
            y = screen_geometry.height() - self.height() - 20
            
            # Set position
            self.move(x, y)
            
            logger.info(f"Notification positioned at ({x}, {y})")
        except Exception as e:
            logger.error(f"Error positioning notification: {e}", exc_info=True)
    
    def fade_out(self):
        """Fade out the notification."""
        try:
            self.fade_animation.start()
            logger.info("Notification fade out started")
        except Exception as e:
            logger.error(f"Error fading out notification: {e}", exc_info=True)
    
    def closeEvent(self, event):
        """Handle close event."""
        try:
            # Stop the timer
            self.timer.stop()
            
            # Stop the animation
            self.fade_animation.stop()
            
            logger.info("Notification closed")
            event.accept()
        except Exception as e:
            logger.error(f"Error during notification close event: {e}", exc_info=True)
            event.accept()
