from typing import Optional
from PyQt6.QtWidgets import (QMainWindow, QWidget, QPushButton, QVBoxLayout, 
                           QComboBox, QLabel, QCheckBox, QSlider, QDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
import pyttsx3
import speech_recognition as sr
import numpy as np
import sounddevice as sd
import pyperclip
import keyboard
from ..utils.audio_processing import AudioProcessor, AudioFormat
from ..utils.logger import logger

class ListenThread(QThread):
    """Thread for handling speech recognition"""
    text_ready = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, recognizer: sr.Recognizer, language: str):
        super().__init__()
        self.recognizer = recognizer
        self.language = language
        self.is_listening = False
        
    def run(self):
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source)
                logger.info("Adjusted for ambient noise")
                
                while self.is_listening:
                    try:
                        audio = self.recognizer.listen(source, timeout=1)
                        text = self.recognizer.recognize_google(
                            audio,
                            language=self.language
                        )
                        self.text_ready.emit(text)
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        logger.error(f"Error in speech recognition: {str(e)}")
                        self.error.emit(str(e))
        except Exception as e:
            logger.error(f"Error in microphone setup: {str(e)}")
            self.error.emit(str(e))

class RecordingThread(QThread):
    """Thread for handling audio recording"""
    data_ready = pyqtSignal(bytes)
    error = pyqtSignal(str)
    
    def __init__(self, sample_rate: int = 44100):
        super().__init__()
        self.sample_rate = sample_rate
        self.is_recording = False
        self.recorded_audio = []
    
    def run(self):
        try:
            # Configure sounddevice with default device
            devices = sd.query_devices()
            default_input = sd.default.device[0]
            if default_input is None:
                for i, dev in enumerate(devices):
                    if dev['max_input_channels'] > 0:
                        default_input = i
                        break
            
            if default_input is None:
                raise RuntimeError("No input device found")
            
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio recording status: {status}")
                if self.is_recording:
                    self.recorded_audio.extend(indata.copy())
                    self.data_ready.emit(indata.tobytes())
            
            with sd.InputStream(device=default_input, channels=1, 
                              samplerate=self.sample_rate, callback=audio_callback):
                while self.is_recording:
                    self.msleep(100)  # Sleep to prevent high CPU usage
        except Exception as e:
            logger.error(f"Recording error: {str(e)}")
            self.error.emit(str(e))
    
    def stop(self):
        self.is_recording = False
        if len(self.recorded_audio) > 0:
            return np.concatenate(self.recorded_audio)
        return None

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
        
        # Noise reduction
        self.noise_checkbox = QCheckBox("Enable Noise Reduction")
        self.noise_checkbox.setChecked(True)
        layout.addWidget(self.noise_checkbox)
        
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

class VoicePlugin(QMainWindow):
    """Plugin for voice-related functionality"""
    def __init__(self):
        super().__init__()
        try:
            self.engine = pyttsx3.init()
            self.recognizer = sr.Recognizer()
            self.audio_processor = AudioProcessor()
            
            # State variables
            self.is_listening = False
            self.is_speaking = False
            self.is_recording = False
            self.current_language = 'en-US'
            self.available_languages = self._get_available_languages()
            
            # Recording setup
            self.recording_thread = None
            self.listen_thread = None
            self.sample_rate = 44100
            
            self.setup_ui()
            self.setup_shortcuts()
            
            logger.info("VoicePlugin initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize VoicePlugin: {str(e)}")
            raise
    
    def _get_available_languages(self):
        """Get available languages for speech recognition"""
        return {
            'en-US': 'English (US)',
            'es-ES': 'Spanish',
            'fr-FR': 'French',
            'de-DE': 'German',
            'it-IT': 'Italian',
            'ja-JP': 'Japanese',
            'ko-KR': 'Korean',
            'zh-CN': 'Chinese (Simplified)',
            'ru-RU': 'Russian'
        }
    
    def setup_ui(self):
        """Set up the user interface"""
        self.setWindowTitle("Voice Controls")
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
        
        # Speech-to-text button
        self.stt_btn = QPushButton("START Audio To Text")
        self.stt_btn.setToolTip("Speech to Text (Ctrl+Shift+S)")
        self.stt_btn.clicked.connect(self.toggle_speech_to_text)
        button_layout.addWidget(self.stt_btn)
        
        # Text-to-speech button
        self.tts_btn = QPushButton("START Text To Audio")
        self.tts_btn.setToolTip("Text to Speech (Ctrl+Shift+T)")
        self.tts_btn.clicked.connect(self.toggle_text_to_speech)
        button_layout.addWidget(self.tts_btn)
        
        layout.addLayout(button_layout)
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        try:
            keyboard.add_hotkey('ctrl+shift+s', self.toggle_speech_to_text)
            keyboard.add_hotkey('ctrl+shift+t', self.toggle_text_to_speech)
            logger.info("Keyboard shortcuts registered")
        except Exception as e:
            logger.error(f"Failed to setup shortcuts: {str(e)}")
    
    def show_settings(self):
        """Show settings dialog"""
        try:
            dialog = VoiceSettingsDialog(self.engine, self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Failed to show settings: {str(e)}")
    
    def toggle_speech_to_text(self):
        """Toggle speech-to-text functionality"""
        if self.is_listening:
            self.stop_listening()
            self.stt_btn.setText("START Audio To Text")
        else:
            self.start_listening()
            self.stt_btn.setText("STOP Audio To Text")
    
    def start_listening(self):
        """Start speech recognition"""
        try:
            self.is_listening = True
            self.stt_btn.setStyleSheet("background-color: #FF3B30;")
            
            self.listen_thread = ListenThread(self.recognizer, self.current_language)
            self.listen_thread.text_ready.connect(self.on_text_recognized)
            self.listen_thread.error.connect(self.on_listen_error)
            self.listen_thread.is_listening = True
            self.listen_thread.start()
            
            logger.info("Started speech recognition")
        except Exception as e:
            logger.error(f"Failed to start listening: {str(e)}")
            self.stop_listening()
    
    def stop_listening(self):
        """Stop speech recognition"""
        try:
            self.is_listening = False
            self.stt_btn.setStyleSheet("")
            
            if self.listen_thread:
                self.listen_thread.is_listening = False
                self.listen_thread.wait()
                self.listen_thread = None
            
            logger.info("Stopped speech recognition")
        except Exception as e:
            logger.error(f"Failed to stop listening: {str(e)}")
    
    def on_text_recognized(self, text: str):
        """Handle recognized text"""
        try:
            keyboard.write(text + ' ')
            logger.info(f"Typed text: {text}")
        except Exception as e:
            logger.error(f"Failed to type text: {str(e)}")
    
    def on_listen_error(self, error_msg: str):
        """Handle listening errors"""
        logger.error(f"Listening error: {error_msg}")
        self.stop_listening()
    
    def toggle_text_to_speech(self):
        """Toggle text-to-speech functionality"""
        if self.is_speaking:
            self.stop_speaking()
            self.tts_btn.setText("START Text To Audio")
        else:
            self.start_speaking()
            self.tts_btn.setText("STOP Text To Audio")
    
    def start_speaking(self):
        """Start text-to-speech"""
        try:
            # Get text from cursor position
            keyboard.send('shift+end')  # Select text from cursor to end
            text = pyperclip.paste()
            keyboard.send('right')  # Clear selection
            
            if text:
                self.is_speaking = True
                self.tts_btn.setStyleSheet("background-color: #007AFF;")
                self.engine.say(text)
                self.engine.runAndWait()
                self.stop_speaking()
            
            logger.info("Started text-to-speech")
        except Exception as e:
            logger.error(f"Failed to start speaking: {str(e)}")
            self.stop_speaking()
    
    def stop_speaking(self):
        """Stop text-to-speech"""
        try:
            self.is_speaking = False
            self.tts_btn.setStyleSheet("")
            self.engine.stop()
            logger.info("Stopped text-to-speech")
        except Exception as e:
            logger.error(f"Failed to stop speaking: {str(e)}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop_listening()
            self.stop_speaking()
            if self.engine:
                self.engine.stop()
            logger.info("VoicePlugin cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
