import sys
import threading
import time
import keyboard
import pyperclip
import speech_recognition as sr
import pyttsx3
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                           QLabel, QComboBox, QSpinBox, QHBoxLayout)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

class VoiceThread(QThread):
    text_ready = pyqtSignal(str)
    error = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = False
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

    def run(self):
        self.running = True
        with self.microphone as source:
            self.status.emit("Adjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source)
            self.status.emit("Ready to listen!")

            while self.running:
                try:
                    audio = self.recognizer.listen(source, timeout=5)
                    text = self.recognizer.recognize_google(audio).lower()
                    
                    if text == "read it":
                        self.text_ready.emit("READ_COMMAND")
                    elif text == "stop":
                        self.text_ready.emit("STOP_COMMAND") 
                    else:
                        self.text_ready.emit(text)
                        
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    self.error.emit(str(e))
                    time.sleep(1)

    def stop(self):
        self.running = False

class VoicePlugin(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.voice_thread = None
        self.tts_engine = pyttsx3.init()
        self.is_reading = False
        self.reading_thread = None

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Settings section
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.clicked.connect(self.toggle_settings)
        layout.addWidget(settings_btn)
        
        # Settings panel (hidden by default)
        self.settings_panel = QWidget()
        settings_layout = QVBoxLayout()
        
        # Voice selection
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        voices = self.get_available_voices()
        self.voice_combo.addItems(voices)
        self.voice_combo.currentTextChanged.connect(self.update_voice_settings)
        voice_layout.addWidget(self.voice_combo)
        settings_layout.addLayout(voice_layout)
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(50, 300)
        self.speed_spin.setValue(150)
        self.speed_spin.valueChanged.connect(self.update_voice_settings)
        speed_layout.addWidget(self.speed_spin)
        settings_layout.addLayout(speed_layout)
        
        self.settings_panel.setLayout(settings_layout)
        self.settings_panel.hide()
        layout.addWidget(self.settings_panel)

        # Control buttons
        self.listen_btn = QPushButton("START Audio To Text")
        self.listen_btn.clicked.connect(self.toggle_listening)
        layout.addWidget(self.listen_btn)

        self.read_btn = QPushButton("START Text To Audio")
        self.read_btn.clicked.connect(self.toggle_reading)
        layout.addWidget(self.read_btn)

        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.setWindowTitle("Voice Controls")

    def get_available_voices(self):
        engine = pyttsx3.init()
        return [voice.name for voice in engine.getProperty('voices')]

    def toggle_settings(self):
        self.settings_panel.setVisible(not self.settings_panel.isVisible())

    def update_voice_settings(self):
        voice_name = self.voice_combo.currentText()
        speed = self.speed_spin.value()
        
        voices = self.tts_engine.getProperty('voices')
        selected_voice = next((v for v in voices if v.name == voice_name), None)
        
        if selected_voice:
            self.tts_engine.setProperty('voice', selected_voice.id)
        self.tts_engine.setProperty('rate', speed)

    def toggle_listening(self):
        if not self.voice_thread or not self.voice_thread.running:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        try:
            self.voice_thread = VoiceThread()
            self.voice_thread.text_ready.connect(self.handle_voice_command)
            self.voice_thread.error.connect(self.handle_error)
            self.voice_thread.status.connect(self.update_status)
            self.voice_thread.start()
            self.listen_btn.setText("STOP Audio To Text")
            self.status_label.setText("Listening...")
        except Exception as e:
            self.handle_error(f"Failed to start listening: {str(e)}")

    def stop_listening(self):
        if self.voice_thread:
            self.voice_thread.stop()
            self.voice_thread = None
        self.listen_btn.setText("START Audio To Text")
        self.status_label.setText("Stopped listening")

    def handle_voice_command(self, text):
        if text == "READ_COMMAND":
            self.start_reading()
        elif text == "STOP_COMMAND":
            self.stop_reading()
        else:
            # Type the recognized text at cursor position
            keyboard.write(text)

    def toggle_reading(self):
        if not self.is_reading:
            self.start_reading()
        else:
            self.stop_reading()

    def start_reading(self):
        if not self.is_reading:
            self.is_reading = True
            self.read_btn.setText("STOP Text To Audio")
            
            # Get selected text from clipboard
            selected_text = pyperclip.paste()
            
            def read_text():
                try:
                    self.tts_engine.say(selected_text)
                    self.tts_engine.runAndWait()
                except Exception as e:
                    self.handle_error(f"Reading error: {str(e)}")
                finally:
                    self.is_reading = False
                    self.read_btn.setText("START Text To Audio")
            
            self.reading_thread = threading.Thread(target=read_text)
            self.reading_thread.start()

    def stop_reading(self):
        if self.is_reading:
            self.is_reading = False
            self.tts_engine.stop()
            if self.reading_thread:
                self.reading_thread.join()
            self.read_btn.setText("START Text To Audio")

    def handle_error(self, error_msg):
        self.status_label.setText(f"Error: {error_msg}")

    def update_status(self, status):
        self.status_label.setText(status)

    def closeEvent(self, event):
        self.stop_listening()
        self.stop_reading()
        super().closeEvent(event)
