from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import QThread, pyqtSignal
import speech_recognition as sr
import sounddevice as sd
import numpy as np
import logging

logger = logging.getLogger('WidgetLogger')

class VoicePlugin(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.is_recording = False
        self.recording_thread = None

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Settings button
        self.settings_btn = QPushButton('⚙️ Settings')
        self.settings_btn.clicked.connect(self.show_settings)
        layout.addWidget(self.settings_btn)

        # Audio to Text button
        self.audio_to_text_btn = QPushButton('START Audio To Text')
        self.audio_to_text_btn.clicked.connect(self.toggle_listening)
        layout.addWidget(self.audio_to_text_btn)

        # Text to Audio button
        self.text_to_audio_btn = QPushButton('START Text To Audio')
        self.text_to_audio_btn.clicked.connect(self.toggle_text_to_speech)
        layout.addWidget(self.text_to_audio_btn)

        # Settings panel (hidden by default)
        self.settings_panel = QWidget()
        settings_layout = QVBoxLayout()
        
        # Device selection
        self.device_label = QLabel('Audio Device:')
        self.device_combo = QComboBox()
        self.update_devices()
        
        settings_layout.addWidget(self.device_label)
        settings_layout.addWidget(self.device_combo)
        self.settings_panel.setLayout(settings_layout)
        self.settings_panel.hide()
        layout.addWidget(self.settings_panel)

        self.setLayout(layout)
        self.setWindowTitle('Voice Controls')
        logger.info('VoicePlugin initialized successfully')

    def update_devices(self):
        try:
            devices = sd.query_devices()
            self.device_combo.clear()
            for i, dev in enumerate(devices):
                self.device_combo.addItem(f"{dev['name']} ({dev['max_input_channels']} in, {dev['max_output_channels']} out)", i)
            logger.info('Voice settings updated')
        except Exception as e:
            logger.error(f'Error updating devices: {str(e)}')

    def show_settings(self):
        if self.settings_panel.isHidden():
            self.settings_panel.show()
            self.settings_btn.setText('⚙️ Hide Settings')
        else:
            self.settings_panel.hide()
            self.settings_btn.setText('⚙️ Settings')

    def toggle_listening(self):
        if not self.is_listening:
            try:
                self.start_listening()
                self.audio_to_text_btn.setText('STOP Audio To Text')
                self.is_listening = True
            except Exception as e:
                logger.error(f'Listening error: {str(e)}')
                self.stop_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        logger.info('Started speech recognition')
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                logger.info('Adjusted for ambient noise')
                audio = self.recognizer.listen(source)
                text = self.recognizer.recognize_google(audio)
                logger.info(f'Recognized text: {text}')
        except Exception as e:
            logger.error(f'Error in speech recognition: {str(e)}')
            raise

    def stop_listening(self):
        self.is_listening = False
        self.audio_to_text_btn.setText('START Audio To Text')
        logger.info('Stopped speech recognition')

    def toggle_text_to_speech(self):
        if not self.is_recording:
            try:
                self.start_recording()
                self.text_to_audio_btn.setText('STOP Text To Audio')
                self.is_recording = True
            except Exception as e:
                logger.error(f'Recording error: {str(e)}')
                self.stop_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        logger.info('Started audio recording')
        try:
            device_idx = self.device_combo.currentData()
            if device_idx is not None:
                # Start recording logic here
                pass
        except Exception as e:
            logger.error(f'Recording error: {str(e)}')
            raise

    def stop_recording(self):
        self.is_recording = False
        self.text_to_audio_btn.setText('START Text To Audio')
        logger.info('Stopped audio recording')
