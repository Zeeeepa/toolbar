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
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio recording status: {status}")
                if self.is_recording:
                    self.recorded_audio.extend(indata.copy())
                    self.data_ready.emit(indata.tobytes())
            
            with sd.InputStream(channels=1, samplerate=self.sample_rate, callback=audio_callback):
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
        self.setGeometry(100, 100, 300, 100)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create buttons
        button_layout = QVBoxLayout()
        
        # Settings button
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self.show_settings)
        button_layout.addWidget(self.settings_btn)
        
        # Speech-to-text button
        self.stt_btn = QPushButton("🎤")
        self.stt_btn.setToolTip("Speech to Text (Ctrl+Shift+S)")
        self.stt_btn.clicked.connect(self.toggle_speech_to_text)
        button_layout.addWidget(self.stt_btn)
        
        # Record button
        self.record_btn = QPushButton("⏺")
        self.record_btn.setToolTip("Record Audio (Ctrl+Shift+R)")
        self.record_btn.clicked.connect(self.toggle_recording)
        button_layout.addWidget(self.record_btn)
        
        # Language selector
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(self.available_languages.keys())
        self.lang_combo.setCurrentText(self.current_language)
        self.lang_combo.currentTextChanged.connect(self.on_language_change)
        button_layout.addWidget(self.lang_combo)
        
        layout.addLayout(button_layout)
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        try:
            keyboard.add_hotkey('ctrl+shift+s', self.toggle_speech_to_text)
            keyboard.add_hotkey('ctrl+shift+r', self.toggle_recording)
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
    
    def on_language_change(self, language: str):
        """Handle language change"""
        try:
            self.current_language = language
            logger.info(f"Language changed to: {language}")
        except Exception as e:
            logger.error(f"Failed to change language: {str(e)}")
    
    def toggle_recording(self):
        """Toggle audio recording"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Start audio recording"""
        try:
            self.is_recording = True
            self.record_btn.setStyleSheet("background-color: #FF3B30;")
            
            self.recording_thread = RecordingThread(self.sample_rate)
            self.recording_thread.is_recording = True
            self.recording_thread.error.connect(self.on_recording_error)
            self.recording_thread.start()
            
            logger.info("Started audio recording")
        except Exception as e:
            logger.error(f"Failed to start recording: {str(e)}")
            self.stop_recording()
    
    def stop_recording(self):
        """Stop audio recording"""
        try:
            self.is_recording = False
            self.record_btn.setStyleSheet("")
            
            if self.recording_thread:
                audio_data = self.recording_thread.stop()
                self.recording_thread.wait()
                self.recording_thread = None
                
                if audio_data is not None:
                    # Process the recorded audio
                    processed_audio = self.audio_processor.process_audio(
                        audio_data.tobytes(),
                        AudioFormat.RAW
                    )
                    self.process_recorded_audio(processed_audio)
            
            logger.info("Stopped audio recording")
        except Exception as e:
            logger.error(f"Failed to stop recording: {str(e)}")
    
    def on_recording_error(self, error_msg: str):
        """Handle recording errors"""
        logger.error(f"Recording error: {error_msg}")
        self.stop_recording()
    
    def process_recorded_audio(self, audio_data: bytes):
        """Process recorded audio data"""
        try:
            # Convert to audio data recognizable by speech_recognition
            audio = sr.AudioData(
                audio_data,
                self.sample_rate,
                2  # sample width in bytes
            )
            
            # Perform speech recognition
            text = self.recognizer.recognize_google(
                audio,
                language=self.current_language
            )
            
            # Type the recognized text
            self.type_text(text)
            logger.info(f"Processed recorded audio: {text}")
        except Exception as e:
            logger.error(f"Failed to process recorded audio: {str(e)}")
    
    def toggle_speech_to_text(self):
        """Toggle speech-to-text functionality"""
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()
    
    def start_listening(self):
        """Start speech recognition"""
        try:
            self.is_listening = True
            self.stt_btn.setStyleSheet("background-color: #007AFF;")
            
            def listen_thread():
                with sr.Microphone() as source:
                    try:
                        # Adjust for ambient noise
                        self.recognizer.adjust_for_ambient_noise(source)
                        logger.info("Adjusted for ambient noise")
                        
                        while self.is_listening:
                            try:
                                audio = self.recognizer.listen(source, timeout=1)
                                text = self.recognizer.recognize_google(
                                    audio,
                                    language=self.current_language
                                )
                                
                                # Process audio through our audio processor
                                processed_audio = self.audio_processor.process_audio(
                                    audio.get_raw_data(),
                                    AudioFormat.RAW
                                )
                                
                                # Type the recognized text
                                self.type_text(text)
                                logger.info(f"Recognized text: {text}")
                                
                            except sr.WaitTimeoutError:
                                continue
                            except Exception as e:
                                logger.error(f"Error in speech recognition: {str(e)}")
                    except Exception as e:
                        logger.error(f"Error in microphone setup: {str(e)}")
                        self.stop_listening()
            
            QThread.create(listen_thread).start()
            logger.info("Started speech recognition")
        except Exception as e:
            logger.error(f"Failed to start listening: {str(e)}")
            self.stop_listening()
    
    def stop_listening(self):
        """Stop speech recognition"""
        try:
            self.is_listening = False
            self.stt_btn.setStyleSheet("")
            logger.info("Stopped speech recognition")
        except Exception as e:
            logger.error(f"Failed to stop listening: {str(e)}")
    
    def type_text(self, text: str):
        """Type the recognized text at the current cursor position"""
        try:
            keyboard.write(text + ' ')
            logger.info(f"Typed text: {text}")
        except Exception as e:
            logger.error(f"Failed to type text: {str(e)}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop_listening()
            self.stop_recording()
            if self.engine:
                self.engine.stop()
            logger.info("VoicePlugin cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
