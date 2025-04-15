import os
import warnings
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QComboBox, QSlider, QPushButton, QFormLayout)
from PyQt5.QtCore import Qt

# Suppress PyQt5 deprecation warnings
warnings.filterwarnings("ignore", message=".*sipPyTypeDict.*")

class ToolbarSettingsDialog(QDialog):
    """Dialog for configuring toolbar settings."""
    
    def __init__(self, config, parent=None):
        """
        Initialize the toolbar settings dialog.
        
        Args:
            config (Config): Application configuration
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Toolbar Settings")
        self.setMinimumSize(400, 300)
        
        self.config = config
        
        # Set up the UI
        self.init_ui()
        
        # Apply dark theme
        self.apply_dark_theme()
        
        # Load current settings
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Create form layout for settings
        form_layout = QFormLayout()
        main_layout.addLayout(form_layout)
        
        # Position setting
        self.position_combo = QComboBox()
        self.position_combo.addItems(["top", "bottom", "left", "right"])
        form_layout.addRow("Position:", self.position_combo)
        
        # Opacity setting
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(10)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setTickInterval(10)
        self.opacity_slider.setTickPosition(QSlider.TicksBelow)
        self.opacity_label = QLabel("90%")
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        form_layout.addRow("Opacity:", opacity_layout)
        
        # Center images setting
        self.center_images_combo = QComboBox()
        self.center_images_combo.addItems(["Yes", "No"])
        form_layout.addRow("Center Images:", self.center_images_combo)
        
        # Stay on top setting
        self.stay_on_top_combo = QComboBox()
        self.stay_on_top_combo.addItems(["Yes", "No"])
        form_layout.addRow("Stay on Top:", self.stay_on_top_combo)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        main_layout.addLayout(buttons_layout)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
    
    def load_settings(self):
        """Load current settings from configuration."""
        # Position
        position = self.config.get('ui', 'position', 'top')
        index = self.position_combo.findText(position)
        if index >= 0:
            self.position_combo.setCurrentIndex(index)
        
        # Opacity
        opacity = float(self.config.get('ui', 'opacity', 0.9))
        self.opacity_slider.setValue(int(opacity * 100))
        
        # Center images
        center_images = self.config.get('ui', 'center_images', True)
        self.center_images_combo.setCurrentIndex(0 if center_images else 1)
        
        # Stay on top
        stay_on_top = self.config.get('ui', 'stay_on_top', True)
        self.stay_on_top_combo.setCurrentIndex(0 if stay_on_top else 1)
    
    def update_opacity_label(self, value):
        """Update the opacity label when the slider changes."""
        self.opacity_label.setText(f"{value}%")
    
    def save_settings(self):
        """Save settings to configuration."""
        # Position
        position = self.position_combo.currentText()
        self.config.set('ui', 'position', position)
        
        # Opacity
        opacity = self.opacity_slider.value() / 100.0
        self.config.set('ui', 'opacity', opacity)
        
        # Center images
        center_images = self.center_images_combo.currentIndex() == 0
        self.config.set('ui', 'center_images', center_images)
        
        # Stay on top
        stay_on_top = self.stay_on_top_combo.currentIndex() == 0
        self.config.set('ui', 'stay_on_top', stay_on_top)
        
        # Accept the dialog
        self.accept()

    def apply_dark_theme(self):
        """Apply a dark theme to the dialog elements."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: #e1e1e1;
            }
            QLabel {
                color: #e1e1e1;
                font-weight: bold;
            }
            QGroupBox {
                color: #e1e1e1;
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 4px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }
            QComboBox {
                background-color: #383838;
                color: #e1e1e1;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox::drop-down {
                border-left: 1px solid #555555;
            }
            QComboBox QAbstractItemView {
                background-color: #383838;
                color: #e1e1e1;
                selection-background-color: #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0086e8;
            }
            QPushButton:pressed {
                background-color: #005fa3;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #383838;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                border: 1px solid #5c5c5c;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #0086e8;
            }
        """)
