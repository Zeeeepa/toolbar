from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton

class GithubPlugin:
    def __init__(self):
        self.name = "github"
        self.dialog = None
        
    def get_widget(self):
        if not self.dialog:
            self.dialog = QDialog()
            layout = QVBoxLayout()
            button = QPushButton("GitHub Actions")
            layout.addWidget(button)
            self.dialog.setLayout(layout)
        return self.dialog
