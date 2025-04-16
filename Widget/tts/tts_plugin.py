import sys
from PyQt5.QtWidgets import QApplication, QPushButton, QMenu
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
import pyttsx3
import keyboard

class TTSThread(QThread):
    finished = pyqtSignal()
    
    def __init__(self, engine, text):
        super().__init__()
        self.engine = engine
        self.text = text
        
    def run(self):
        self.engine.say(self.text)
        self.engine.runAndWait()
        self.finished.emit()

class TTSPlugin:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.is_playing = False
        self.tts_thread = None
        self.setup_shortcut()
        
    def setup_shortcut(self):
        # Register Ctrl+Shift+T shortcut for reading selected text
        keyboard.add_hotkey('ctrl+shift+t', self.read_selected_text)
        
    def create_button(self, toolbar):
        self.button = QPushButton()
        self.button.setIcon(QIcon('Toolbar/ui/icons/tts.png'))
        self.button.setToolTip('Text to Speech (Ctrl+Shift+T)')
        
        # Create context menu
        menu = QMenu()
        play_action = menu.addAction('Play/Pause')
        stop_action = menu.addAction('Stop')
        
        play_action.triggered.connect(self.toggle_play_pause)
        stop_action.triggered.connect(self.stop)
        
        self.button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.button.customContextMenuRequested.connect(lambda pos: menu.exec_(self.button.mapToGlobal(pos)))
        
        # Connect main button click
        self.button.clicked.connect(self.read_selected_text)
        
        return self.button
    
    def get_selected_text(self):
        clipboard = QApplication.clipboard()
        clipboard.clear()
        keyboard.send('ctrl+c')
        QThread.msleep(100)  # Give time for clipboard to update
        text = clipboard.text()
        return text
    
    def read_selected_text(self):
        text = self.get_selected_text()
        if text:
            if self.is_playing:
                self.stop()
            self.start_tts(text)
    
    def start_tts(self, text):
        self.tts_thread = TTSThread(self.engine, text)
        self.tts_thread.finished.connect(self.on_tts_finished)
        self.tts_thread.start()
        self.is_playing = True
        self.button.setStyleSheet('background-color: #90EE90;')  # Light green when playing
    
    def toggle_play_pause(self):
        if self.is_playing:
            self.engine.stop()
            self.is_playing = False
            self.button.setStyleSheet('')
        else:
            self.engine.resume()
            self.is_playing = True
            self.button.setStyleSheet('background-color: #90EE90;')
    
    def stop(self):
        if self.is_playing:
            self.engine.stop()
            if self.tts_thread:
                self.tts_thread.quit()
                self.tts_thread.wait()
            self.is_playing = False
            self.button.setStyleSheet('')
    
    def on_tts_finished(self):
        self.is_playing = False
        self.button.setStyleSheet('')
