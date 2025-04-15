import os
import requests
import base64
from io import BytesIO
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QDialog, QLineEdit, QFileDialog, QMessageBox, QComboBox,
    QGridLayout, QScrollArea, QFrame
)
from PyQt5.QtGui import QPixmap, QIcon, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QBuffer

class ProjectIconDialog(QDialog):
    """
    Dialog for setting a project icon.
    Allows users to enter a URL or select a local image file.
    """
    
    def __init__(self, parent=None, project_name="", current_icon_url=None):
        """
        Initialize the project icon dialog.
        
        Args:
            parent: Parent widget
            project_name: Name of the project
            current_icon_url: Current icon URL if any
        """
        super().__init__(parent)
        self.project_name = project_name
        self.current_icon_url = current_icon_url
        self.icon_url = None
        self.icon_data = None  # For storing base64 encoded image data
        
        self.setWindowTitle(f"Set Icon for {project_name}")
        self.setMinimumWidth(500)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("Icon URL:")
        self.url_input = QLineEdit()
        if self.current_icon_url:
            self.url_input.setText(self.current_icon_url)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        
        # Browse button
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_file)
        url_layout.addWidget(browse_button)
        
        layout.addLayout(url_layout)
        
        # Icon type selection
        type_layout = QHBoxLayout()
        type_label = QLabel("Icon Type:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["URL", "Local File", "Default Icon", "Generated Icon"])
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        
        layout.addLayout(type_layout)
        
        # Preview area
        preview_layout = QVBoxLayout()
        preview_label = QLabel("Preview:")
        self.icon_preview = QLabel()
        self.icon_preview.setAlignment(Qt.AlignCenter)
        self.icon_preview.setMinimumSize(100, 100)
        self.icon_preview.setMaximumSize(100, 100)
        self.icon_preview.setStyleSheet("border: 1px solid #ccc;")
        
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.icon_preview, alignment=Qt.AlignCenter)
        
        layout.addLayout(preview_layout)
        
        # Default icons grid
        self.default_icons_container = QWidget()
        self.default_icons_container.setVisible(False)
        default_icons_layout = QVBoxLayout(self.default_icons_container)
        
        default_icons_label = QLabel("Select a default icon:")
        default_icons_layout.addWidget(default_icons_label)
        
        # Create a scroll area for default icons
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        default_icons_widget = QWidget()
        self.default_icons_grid = QGridLayout(default_icons_widget)
        self.default_icons_grid.setSpacing(10)
        
        # Add default icons
        self.add_default_icons()
        
        scroll_area.setWidget(default_icons_widget)
        default_icons_layout.addWidget(scroll_area)
        
        layout.addWidget(self.default_icons_container)
        
        # Generated icon options
        self.generated_icon_container = QWidget()
        self.generated_icon_container.setVisible(False)
        generated_icon_layout = QVBoxLayout(self.generated_icon_container)
        
        generated_icon_label = QLabel("Generate an icon from the project name:")
        generated_icon_layout.addWidget(generated_icon_label)
        
        # Color selection
        color_layout = QHBoxLayout()
        color_label = QLabel("Background Color:")
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Blue", "Green", "Red", "Purple", "Orange", "Teal"])
        self.color_combo.currentIndexChanged.connect(self.generate_icon)
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_combo)
        
        generated_icon_layout.addLayout(color_layout)
        
        # Generate button
        generate_button = QPushButton("Generate Icon")
        generate_button.clicked.connect(self.generate_icon)
        generated_icon_layout.addWidget(generate_button)
        
        layout.addWidget(self.generated_icon_container)
        
        # Load preview if URL exists
        if self.current_icon_url:
            self.load_preview(self.current_icon_url)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.preview_button = QPushButton("Preview")
        self.preview_button.clicked.connect(self.preview_icon)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_icon)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.preview_button)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def add_default_icons(self):
        """Add default icons to the grid."""
        # Define default icon paths
        icon_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "icons")
        
        # List of default icons
        default_icons = [
            "github.svg", "project.svg", "script.svg", "notification.svg",
            "settings.svg", "linear.svg", "exit.svg"
        ]
        
        # Add icons to grid
        row, col = 0, 0
        for icon_name in default_icons:
            icon_path = os.path.join(icon_dir, icon_name)
            if os.path.exists(icon_path):
                button = QPushButton()
                button.setIcon(QIcon(icon_path))
                button.setIconSize(QSize(32, 32))
                button.setFixedSize(50, 50)
                button.setToolTip(icon_name)
                button.clicked.connect(lambda checked=False, path=icon_path: self.select_default_icon(path))
                
                self.default_icons_grid.addWidget(button, row, col)
                
                col += 1
                if col > 3:  # 4 icons per row
                    col = 0
                    row += 1
    
    def select_default_icon(self, icon_path):
        """Select a default icon."""
        self.load_preview(icon_path)
        self.icon_url = icon_path
    
    def on_type_changed(self, index):
        """Handle icon type selection change."""
        # Hide all containers first
        self.default_icons_container.setVisible(False)
        self.generated_icon_container.setVisible(False)
        
        # Show appropriate container based on selection
        if index == 2:  # Default Icon
            self.default_icons_container.setVisible(True)
        elif index == 3:  # Generated Icon
            self.generated_icon_container.setVisible(True)
            self.generate_icon()
    
    def generate_icon(self):
        """Generate an icon from the project name."""
        if not self.project_name:
            return
        
        # Get first letter of project name
        letter = self.project_name[0].upper()
        
        # Get selected color
        color_name = self.color_combo.currentText()
        color_map = {
            "Blue": "#3498db",
            "Green": "#2ecc71",
            "Red": "#e74c3c",
            "Purple": "#9b59b6",
            "Orange": "#e67e22",
            "Teal": "#1abc9c"
        }
        bg_color = color_map.get(color_name, "#3498db")
        
        # Create a QImage for the icon
        size = 100
        image = QImage(size, size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        # Draw background circle
        import math
        from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(bg_color)))
        painter.drawEllipse(0, 0, size, size)
        
        # Draw text
        font = QFont("Arial", size // 2)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor("white")))
        painter.drawText(0, 0, size, size, Qt.AlignCenter, letter)
        
        painter.end()
        
        # Convert to pixmap for preview
        pixmap = QPixmap.fromImage(image)
        self.icon_preview.setPixmap(pixmap)
        
        # Convert to base64 for storage
        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        image.save(buffer, "PNG")
        image_data = buffer.data()
        self.icon_data = base64.b64encode(image_data).decode('utf-8')
        
        # Set icon URL to data URL
        self.icon_url = f"data:image/png;base64,{self.icon_data}"
    
    def browse_file(self):
        """Open file dialog to select an image file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon Image", "", "Image Files (*.png *.jpg *.jpeg *.gif *.svg)"
        )
        
        if file_path:
            # Set the file path in the URL field
            self.url_input.setText(file_path)
            self.load_preview(file_path)
            
            # Set combo box to "Local File"
            self.type_combo.setCurrentIndex(1)
    
    def preview_icon(self):
        """Preview the icon from the URL."""
        url = self.url_input.text().strip()
        if url:
            self.load_preview(url)
        else:
            QMessageBox.warning(self, "Warning", "Please enter an icon URL.")
    
    def load_preview(self, url):
        """
        Load and display the icon preview.
        
        Args:
            url: URL or file path of the icon
        """
        try:
            pixmap = QPixmap()
            
            # Check if it's a local file or URL
            if os.path.isfile(url):
                pixmap.load(url)
                self.icon_url = url
            elif url.startswith("data:image"):
                # Handle data URL
                data = url.split(",")[1]
                image_data = base64.b64decode(data)
                pixmap.loadFromData(image_data)
                self.icon_url = url
            else:
                # Download from URL
                response = requests.get(url)
                if response.status_code == 200:
                    pixmap.loadFromData(response.content)
                    self.icon_url = url
                else:
                    QMessageBox.warning(self, "Warning", f"Failed to load image: {response.status_code}")
                    return
            
            if not pixmap.isNull():
                # Scale the pixmap to fit the preview area
                pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.icon_preview.setPixmap(pixmap)
            else:
                QMessageBox.warning(self, "Warning", "Invalid image format.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading image: {str(e)}")
    
    def accept_icon(self):
        """Accept the icon URL and close the dialog."""
        # If URL input is empty but we have a generated icon or default icon
        if not self.url_input.text().strip() and self.icon_url:
            self.accept()
            return
            
        url = self.url_input.text().strip()
        if url:
            self.icon_url = url
            self.accept()
        else:
            QMessageBox.warning(self, "Warning", "Please enter an icon URL or select/generate an icon.")

class ProjectIconWidget(QWidget):
    """
    Widget for displaying a project icon.
    Clicking on the icon allows changing it.
    """
    
    icon_changed = pyqtSignal(str, str)  # project_name, icon_url
    
    def __init__(self, parent=None, project_name="", project_full_name="", icon_url=None):
        """
        Initialize the project icon widget.
        
        Args:
            parent: Parent widget
            project_name: Name of the project
            project_full_name: Full name of the project (owner/repo)
            icon_url: URL to the icon image
        """
        super().__init__(parent)
        self.project_name = project_name
        self.project_full_name = project_full_name
        self.icon_url = icon_url
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Icon button
        self.icon_button = QPushButton()
        self.icon_button.setFixedSize(48, 48)
        self.icon_button.setIconSize(QSize(32, 32))
        self.icon_button.setToolTip(f"Click to change icon for {self.project_name}")
        self.icon_button.clicked.connect(self.change_icon)
        
        # Set initial icon if available
        if self.icon_url:
            self.set_icon(self.icon_url)
        else:
            # Default icon
            self.icon_button.setText(self.project_name[0].upper())
        
        layout.addWidget(self.icon_button, alignment=Qt.AlignCenter)
        
        # Project name label
        name_label = QLabel(self.project_name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setMaximumWidth(80)
        
        layout.addWidget(name_label, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)
        
    def set_icon(self, url):
        """
        Set the icon from a URL.
        
        Args:
            url: URL to the icon image
        """
        try:
            self.icon_url = url
            
            # Check if it's a data URL
            if url and url.startswith("data:image"):
                try:
                    data = url.split(",")[1]
                    image_data = base64.b64decode(data)
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_data)
                except Exception as e:
                    print(f"Error loading data URL: {e}")
                    pixmap = None
            # Check if it's a local file or URL
            elif os.path.isfile(url):
                pixmap = QPixmap(url)
            else:
                # Download from URL
                response = requests.get(url)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                else:
                    print(f"Failed to load image: {response.status_code}")
                    pixmap = None
            
            if pixmap and not pixmap.isNull():
                icon = QIcon(pixmap)
                self.icon_button.setIcon(icon)
                self.icon_button.setText("")  # Clear text when icon is set
            else:
                print("Invalid image format or failed to load image")
                # Fallback to text
                self.icon_button.setText(self.project_name[0].upper())
                self.icon_button.setIcon(QIcon())
        except Exception as e:
            print(f"Error setting icon: {e}")
            # Fallback to text
            self.icon_button.setText(self.project_name[0].upper())
            self.icon_button.setIcon(QIcon())
    
    def change_icon(self):
        """Open dialog to change the project icon."""
        dialog = ProjectIconDialog(self, self.project_name, self.icon_url)
        if dialog.exec_() == QDialog.Accepted and dialog.icon_url:
            self.set_icon(dialog.icon_url)
            self.icon_changed.emit(self.project_full_name, dialog.icon_url)
