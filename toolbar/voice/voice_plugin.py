import sys
import os
import logging
import keyboard
import pyperclip
import pyttsx3
import speech_recognition as sr
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal

logger = logging.getLogger('WidgetLogger')

class VoiceThread(QThread):
    text_ready = pyqtSignal(str)
    error = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.recognizer = sr.Recognizer()
        self.is_running = False
        
    def run(self):
        self.is_running = True
        try:
            with sr.Microphone() as source:
                self.status.emit("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source)
                self.status.emit("Listening...")
                
                while self.is_running:
                    try:
                        audio = self.recognizer.listen(source, timeout=5)
                        text = self.recognizer.recognize_google(audio)
                        self.text_ready.emit(text + " ")
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except Exception as e:
                        self.error.emit(str(e))
                        break
                        
        except Exception as e:
            self.error.emit(str(e))
        
        self.is_running = False
        self.status.emit("Stopped")

class TTSThread(QThread):
    error = pyqtSignal(str)
    status = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = pyttsx3.init()
        self.text = ""
        self.is_running = False
        
    def set_text(self, text):
        self.text = text
        
    def run(self):
        self.is_running = True
        try:
            self.status.emit("Reading text...")
            self.engine.say(self.text)
            self.engine.runAndWait()
        except Exception as e:
            self.error.emit(str(e))
        
        self.is_running = False
        self.status.emit("Stopped")

class VoicePlugin(QWidget):
    def __init__(self):
        super().__init__()
        self.voice_thread = VoiceThread()
        self.tts_thread = TTSThread()
        self.setup_ui()
        self.setup_connections()
        logger.info("VoicePlugin initialized successfully")

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Settings button
        self.settings_btn = QPushButton("⚙️ Settings")
        layout.addWidget(self.settings_btn)
        
        # Voice settings
        self.voice_settings = QWidget()
        voice_layout = QVBoxLayout()
        
        # Voice selection
        voice_label = QLabel("Voice:")
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["Default"] + [voice.name for voice in self.tts_thread.engine.getProperty('voices')])
        
        # Speed selection
        speed_label = QLabel("Speed:")
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        
        voice_layout.addWidget(voice_label)
        voice_layout.addWidget(self.voice_combo)
        voice_layout.addWidget(speed_label)
        voice_layout.addWidget(self.speed_combo)
        self.voice_settings.setLayout(voice_layout)
        self.voice_settings.hide()
        layout.addWidget(self.voice_settings)
        
        # Audio to Text button
        self.stt_btn = QPushButton("START Audio To Text")
        layout.addWidget(self.stt_btn)
        
        # Text to Audio button
        self.tts_btn = QPushButton("START Text To Audio")
        layout.addWidget(self.tts_btn)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.setWindowTitle("Voice Controls")
        self.setFixedWidth(300)

    def setup_connections(self):
        # Settings
        self.settings_btn.clicked.connect(self.toggle_settings)
        self.voice_combo.currentTextChanged.connect(self.update_voice_settings)
        self.speed_combo.currentTextChanged.connect(self.update_voice_settings)
        
        # Speech to Text
        self.voice_thread.text_ready.connect(self.handle_text)
        self.voice_thread.error.connect(self.handle_error)
        self.voice_thread.status.connect(self.update_status)
        self.stt_btn.clicked.connect(self.toggle_listening)
        
        # Text to Speech
        self.tts_thread.error.connect(self.handle_error)
        self.tts_thread.status.connect(self.update_status)
        self.tts_btn.clicked.connect(self.toggle_reading)

    def toggle_settings(self):
        if self.voice_settings.isVisible():
            self.voice_settings.hide()
        else:
            self.voice_settings.show()

    def update_voice_settings(self):
        try:
            # Update voice
            voice_name = self.voice_combo.currentText()
            if voice_name != "Default":
                for voice in self.tts_thread.engine.getProperty('voices'):
                    if voice.name == voice_name:
                        self.tts_thread.engine.setProperty('voice', voice.id)
                        break
            
            # Update speed
            speed = float(self.speed_combo.currentText().replace('x', ''))
            self.tts_thread.engine.setProperty('rate', 150 * speed)
            
            logger.info("Voice settings updated")
        except Exception as e:
            logger.error(f"Failed to update voice settings: {str(e)}")

    def toggle_listening(self):
        if not self.voice_thread.is_running:
            self.stt_btn.setText("STOP Audio To Text")
            self.voice_thread.start()
        else:
            self.voice_thread.is_running = False
            self.stt_btn.setText("START Audio To Text")

    def toggle_reading(self):
        if not self.tts_thread.is_running:
            # Get selected text
            keyboard.send('ctrl+c')  # Simulate Ctrl+C to copy selected text
            selected_text = pyperclip.paste()
            
            if selected_text:
                self.tts_btn.setText("STOP Text To Audio")
                self.tts_thread.set_text(selected_text)
                self.tts_thread.start()
            else:
                self.update_status("No text selected")
        else:
            self.tts_thread.is_running = False
            self.tts_thread.engine.stop()
            self.tts_btn.setText("START Text To Audio")

    def handle_text(self, text):
        # Type the recognized text at cursor position
        keyboard.write(text)

    def handle_error(self, error):
        logger.error(f"Error: {error}")
        self.update_status(f"Error: {error}")
        
        # Reset buttons
        self.stt_btn.setText("START Audio To Text")
        self.tts_btn.setText("START Text To Audio")

    def update_status(self, status):
        self.status_label.setText(status)
        logger.info(status)
