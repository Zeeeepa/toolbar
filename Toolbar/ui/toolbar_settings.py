import os
import warnings
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QComboBox, QSlider, QPushButton, QFormLayout,
                           QGroupBox, QRadioButton, QButtonGroup, QCheckBox)
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
        self.setMinimumSize(450, 350)
        
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
        position_group = QGroupBox("Toolbar Position")
        position_layout = QVBoxLayout(position_group)
        
        self.position_top = QRadioButton("Top")
        self.position_bottom = QRadioButton("Bottom")
        self.position_left = QRadioButton("Left")
        self.position_right = QRadioButton("Right")
        
        self.position_group = QButtonGroup(self)
        self.position_group.addButton(self.position_top, 1)
        self.position_group.addButton(self.position_bottom, 2)
        self.position_group.addButton(self.position_left, 3)
        self.position_group.addButton(self.position_right, 4)
        
        position_layout.addWidget(self.position_top)
        position_layout.addWidget(self.position_bottom)
        position_layout.addWidget(self.position_left)
        position_layout.addWidget(self.position_right)
        
        form_layout.addRow(position_group)
        
        # Opacity setting
        opacity_group = QGroupBox("Transparency")
        opacity_layout = QVBoxLayout(opacity_group)
        
        opacity_slider_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(10)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setTickInterval(10)
        self.opacity_slider.setTickPosition(QSlider.TicksBelow)
        self.opacity_label = QLabel("90%")
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        opacity_slider_layout.addWidget(self.opacity_slider)
        opacity_slider_layout.addWidget(self.opacity_label)
        
        opacity_layout.addLayout(opacity_slider_layout)
        opacity_layout.addWidget(QLabel("Move slider left for more transparency, right for more opacity"))
        
        form_layout.addRow(opacity_group)
        
        # Behavior settings
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout(behavior_group)
        
        # Stay on top setting
        self.stay_on_top_checkbox = QCheckBox("Stay on top of other windows")
        behavior_layout.addWidget(self.stay_on_top_checkbox)
        
        # Center images setting
        self.center_images_checkbox = QCheckBox("Center images in toolbar")
        behavior_layout.addWidget(self.center_images_checkbox)
        
        form_layout.addRow(behavior_group)
        
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
        if position == 'top':
            self.position_top.setChecked(True)
        elif position == 'bottom':
            self.position_bottom.setChecked(True)
        elif position == 'left':
            self.position_left.setChecked(True)
        elif position == 'right':
            self.position_right.setChecked(True)
        
        # Opacity
        opacity = float(self.config.get('ui', 'opacity', 0.9))
        self.opacity_slider.setValue(int(opacity * 100))
        
        # Center images
        center_images = self.config.get('ui', 'center_images', True)
        self.center_images_checkbox.setChecked(center_images)
        
        # Stay on top
        stay_on_top = self.config.get('ui', 'stay_on_top', True)
        self.stay_on_top_checkbox.setChecked(stay_on_top)
    
    def update_opacity_label(self, value):
        """Update the opacity label when the slider changes."""
        self.opacity_label.setText(f"{value}%")
    
    def save_settings(self):
        """Save settings to configuration."""
        # Position
        if self.position_top.isChecked():
            position = 'top'
        elif self.position_bottom.isChecked():
            position = 'bottom'
        elif self.position_left.isChecked():
            position = 'left'
        elif self.position_right.isChecked():
            position = 'right'
        else:
            position = 'top'  # Default
        
        self.config.set('ui', 'position', position)
        
        # Opacity
        opacity = self.opacity_slider.value() / 100.0
        self.config.set('ui', 'opacity', opacity)
        
        # Center images
        center_images = self.center_images_checkbox.isChecked()
        self.config.set('ui', 'center_images', center_images)
        
        # Stay on top
        stay_on_top = self.stay_on_top_checkbox.isChecked()
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
            QRadioButton {
                color: #e1e1e1;
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 13px;
                height: 13px;
            }
            QRadioButton::indicator:checked {
                background-color: #0078d4;
                border: 2px solid #e1e1e1;
                border-radius: 7px;
            }
            QRadioButton::indicator:unchecked {
                background-color: #383838;
                border: 2px solid #e1e1e1;
                border-radius: 7px;
            }
            QCheckBox {
                color: #e1e1e1;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 2px solid #e1e1e1;
                border-radius: 3px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #383838;
                border: 2px solid #e1e1e1;
                border-radius: 3px;
            }
        """)
