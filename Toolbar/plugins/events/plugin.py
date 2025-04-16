from PyQt6.QtWidgets import QWidget

class EventsPlugin:
    def __init__(self):
        self.name = "events"
        self.widget = None
        
    def get_widget(self):
        if not self.widget:
            self.widget = QWidget()
        return self.widget
