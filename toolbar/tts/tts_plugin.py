import sys
from typing import Optional
from PyQt6.QtWidgets import QApplication, QPushButton, QMenu, QWidget, QMainWindow, QVBoxLayout
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
import pyttsx3
import keyboard
from ..utils.audio_processing import AudioProcessor, AudioFormat
from ..utils.logger import logger

class TTSThread(QThread):
    """Thread for handling text-to-speech operations"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, engine: pyttsx3.Engine, text: str):
        super().__init__()
        self.engine = engine
        self.text = text
        
    def run(self):
        try:
            self.engine.say(self.text)
            self.engine.runAndWait()
            self.finished.emit()
        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            self.error.emit(str(e))

class TTSPlugin(QMainWindow):
    """Plugin for text-to-speech functionality"""
    def __init__(self):
        super().__init__()
        try:
            self.engine = pyttsx3.init()
            self.audio_processor = AudioProcessor()
            self.is_playing = False
            self.tts_thread: Optional[TTSThread] = None
            self.setup_ui()
            self.setup_shortcut()
        except Exception as e:
            logger.error(f"Failed to initialize TTS plugin: {str(e)}")
            raise
    
    def setup_ui(self):
        """Set up the user interface"""
        self.setWindowTitle("Text to Speech")
        self.setGeometry(100, 100, 200, 100)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create TTS button
        self.button = QPushButton()
        self.button.setIcon(QIcon('toolbar/ui/icons/tts.png'))
        self.button.setToolTip('Text to Speech (Ctrl+Shift+T)')
        layout.addWidget(self.button)
        
        # Create context menu
        menu = QMenu()
        play_action = menu.addAction('Play/Pause')
        stop_action = menu.addAction('Stop')
        settings_action = menu.addAction('Settings')
        
        play_action.triggered.connect(self.toggle_play_pause)
        stop_action.triggered.connect(self.stop)
        settings_action.triggered.connect(self.show_settings)
        
        self.button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.button.customContextMenuRequested.connect(
            lambda pos: menu.exec(self.button.mapToGlobal(pos))
        )
        
        self.button.clicked.connect(self.read_selected_text)
        
    def setup_shortcut(self):
        """Set up keyboard shortcuts"""
        try:
            keyboard.add_hotkey('ctrl+shift+t', self.read_selected_text)
            logger.info("TTS shortcuts registered successfully")
        except Exception as e:
            logger.error(f"Failed to register TTS shortcuts: {str(e)}")
            
    def get_selected_text(self) -> str:
        """Get the currently selected text"""
        try:
            clipboard = QApplication.clipboard()
            clipboard.clear()
            keyboard.send('ctrl+c')
            QThread.msleep(100)  # Give time for clipboard to update
            return clipboard.text()
        except Exception as e:
            logger.error(f"Failed to get selected text: {str(e)}")
            return ""
    
    def read_selected_text(self):
        """Read the selected text using TTS"""
        text = self.get_selected_text()
        if text:
            if self.is_playing:
                self.stop()
            self.start_tts(text)
    
    def start_tts(self, text: str):
        """Start the TTS process for the given text"""
        try:
            self.tts_thread = TTSThread(self.engine, text)
            self.tts_thread.finished.connect(self.on_tts_finished)
            self.tts_thread.error.connect(self.on_tts_error)
            self.tts_thread.start()
            self.is_playing = True
            self.update_button_state(True)
        except Exception as e:
            logger.error(f"Failed to start TTS: {str(e)}")
            self.on_tts_error(str(e))
    
    def toggle_play_pause(self):
        """Toggle between play and pause states"""
        try:
            if self.is_playing:
                self.engine.stop()
                self.is_playing = False
                self.update_button_state(False)
            else:
                self.engine.resume()
                self.is_playing = True
                self.update_button_state(True)
        except Exception as e:
            logger.error(f"Failed to toggle play/pause: {str(e)}")
    
    def stop(self):
        """Stop the TTS playback"""
        try:
            if self.is_playing:
                self.engine.stop()
                if self.tts_thread:
                    self.tts_thread.quit()
                    self.tts_thread.wait()
                self.is_playing = False
                self.update_button_state(False)
        except Exception as e:
            logger.error(f"Failed to stop TTS: {str(e)}")
    
    def update_button_state(self, is_active: bool):
        """Update the button appearance based on state"""
        if self.button:
            self.button.setStyleSheet(
                'background-color: #90EE90;' if is_active else ''
            )
    
    def on_tts_finished(self):
        """Handle TTS completion"""
        self.is_playing = False
        self.update_button_state(False)
        logger.info("TTS playback completed")
    
    def on_tts_error(self, error_msg: str):
        """Handle TTS errors"""
        self.is_playing = False
        self.update_button_state(False)
        logger.error(f"TTS error: {error_msg}")
    
    def show_settings(self):
        """Show TTS settings dialog"""
        # TODO: Implement settings dialog
        pass

    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop()
            self.engine.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
