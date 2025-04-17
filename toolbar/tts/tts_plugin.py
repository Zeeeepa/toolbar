import sys
from typing import Optional
from PyQt6.QtWidgets import QApplication, QPushButton, QMenu, QWidget, QMainWindow, QVBoxLayout, QDialog, QComboBox, QSlider, QLabel, QPushButton
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
import pyttsx3
import keyboard
import pyperclip
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
        self.setGeometry(100, 100, 300, 150)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create buttons
        button_layout = QVBoxLayout()
        
        # Settings button
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.setToolTip("Voice and Audio Settings")
        self.settings_btn.clicked.connect(self.show_settings)
        button_layout.addWidget(self.settings_btn)
        
        # Text-to-speech button
        self.tts_btn = QPushButton("START Text To Audio")
        self.tts_btn.setToolTip("Text to Speech (Ctrl+Shift+T)")
        self.tts_btn.clicked.connect(self.toggle_text_to_speech)
        button_layout.addWidget(self.tts_btn)
        
        layout.addLayout(button_layout)
        
    def setup_shortcut(self):
        """Set up keyboard shortcuts"""
        try:
            keyboard.add_hotkey('ctrl+shift+t', self.toggle_text_to_speech)
            logger.info("TTS shortcuts registered successfully")
        except Exception as e:
            logger.error(f"Failed to register TTS shortcuts: {str(e)}")
            
    def get_text_from_cursor(self) -> str:
        """Get text from cursor position to end"""
        try:
            # Save current clipboard content
            old_clipboard = pyperclip.paste()
            
            # Select text from cursor to end and copy
            keyboard.send('shift+end')
            keyboard.send('ctrl+c')
            text = pyperclip.paste()
            
            # Restore clipboard and clear selection
            pyperclip.copy(old_clipboard)
            keyboard.send('right')
            
            return text
        except Exception as e:
            logger.error(f"Failed to get text from cursor: {str(e)}")
            return ""
    
    def toggle_text_to_speech(self):
        """Toggle text-to-speech functionality"""
        if self.is_playing:
            self.stop_tts()
            self.tts_btn.setText("START Text To Audio")
        else:
            text = self.get_text_from_cursor()
            if text:
                self.start_tts(text)
                self.tts_btn.setText("STOP Text To Audio")
    
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
    
    def stop_tts(self):
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
        if self.tts_btn:
            self.tts_btn.setStyleSheet(
                'background-color: #007AFF;' if is_active else ''
            )
    
    def on_tts_finished(self):
        """Handle TTS completion"""
        self.is_playing = False
        self.update_button_state(False)
        self.tts_btn.setText("START Text To Audio")
        logger.info("TTS playback completed")
    
    def on_tts_error(self, error_msg: str):
        """Handle TTS errors"""
        self.is_playing = False
        self.update_button_state(False)
        self.tts_btn.setText("START Text To Audio")
        logger.error(f"TTS error: {error_msg}")
    
    def show_settings(self):
        """Show TTS settings dialog"""
        try:
            dialog = VoiceSettingsDialog(self.engine, self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Failed to show settings: {str(e)}")

    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop_tts()
            self.engine.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

class VoiceSettingsDialog(QDialog):
    """Dialog for voice settings"""
    def __init__(self, engine: pyttsx3.Engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Voice Settings")
        self.setGeometry(100, 100, 300, 400)
        
        layout = QVBoxLayout(self)
        
        # Voice selection
        layout.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        voices = self.engine.getProperty('voices')
        self.voice_combo.addItems([v.id for v in voices])
        layout.addWidget(self.voice_combo)
        
        # Speed control
        layout.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(100, 300)
        self.speed_slider.setValue(self.engine.getProperty('rate'))
        layout.addWidget(self.speed_slider)
        
        # Volume control
        layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.engine.getProperty('volume') * 100))
        layout.addWidget(self.volume_slider)
        
        # Apply button
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_settings)
        layout.addWidget(apply_btn)
    
    def apply_settings(self):
        try:
            self.engine.setProperty('voice', self.voice_combo.currentText())
            self.engine.setProperty('rate', self.speed_slider.value())
            self.engine.setProperty('volume', self.volume_slider.value() / 100)
            self.accept()
            logger.info("Voice settings updated")
        except Exception as e:
            logger.error(f"Failed to apply settings: {str(e)}")
