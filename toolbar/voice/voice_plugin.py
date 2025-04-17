import sys
import logging
import keyboard
import pyperclip
import speech_recognition as sr
import pyttsx3
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QComboBox,
    QLabel, QSpinBox, QProgressBar, QSystemTrayIcon,
    QMenu, QApplication
)

logger = logging.getLogger('WidgetLogger')

class TranscriptionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.running = False
        self._cache = {}

    def run(self):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                logger.info("Adjusted for ambient noise")
                
                while self.running:
                    try:
                        audio = self.recognizer.listen(source, timeout=5)
                        
                        # Use cache if available
                        audio_data = audio.get_raw_data()
                        if audio_data in self._cache:
                            text = self._cache[audio_data]
                        else:
                            text = self.recognizer.recognize_google(audio)
                            self._cache[audio_data] = text
                            
                        if text:
                            self.finished.emit(text)
                            
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        self.error.emit(str(e))
                        logger.error(f"Error in speech recognition: {str(e)}")
                        
        except Exception as e:
            self.error.emit(str(e))
            logger.error(f"Error in microphone setup: {str(e)}")

    def stop(self):
        self.running = False

class TTSThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, text, rate, voice):
        super().__init__()
        self.text = text
        self.rate = rate
        self.voice = voice
        self.engine = None
        self.running = True

    def run(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            
            voices = self.engine.getProperty('voices')
            for v in voices:
                if self.voice in v.name:
                    self.engine.setProperty('voice', v.id)
                    break
            
            # Split text into sentences for progress updates
            sentences = self.text.split('.')
            total = len(sentences)
            
            for i, sentence in enumerate(sentences):
                if not self.running:
                    break
                    
                if sentence.strip():
                    self.engine.say(sentence)
                    self.engine.runAndWait()
                    
                progress = int((i + 1) / total * 100)
                self.progress.emit(progress)
                
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
            logger.error(f"TTS Error: {str(e)}")

    def stop(self):
        self.running = False
        if self.engine:
            self.engine.stop()

class VoicePlugin(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('Toolbar', 'VoicePlugin')
        self.transcription_thread = None
        self.tts_thread = None
        self.setup_ui()
        self.setup_tray()
        self.load_settings()
        logger.info("VoicePlugin initialized successfully")

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Settings button
        self.settings_btn = QPushButton('⚙️ Settings')
        self.settings_btn.setToolTip('Configure voice settings')
        self.settings_btn.clicked.connect(self.toggle_settings)
        layout.addWidget(self.settings_btn)

        # Settings panel (hidden by default)
        self.settings_panel = QWidget()
        settings_layout = QVBoxLayout()
        
        # Voice selection
        self.voice_label = QLabel('Voice:')
        self.voice_combo = QComboBox()
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        for voice in voices:
            self.voice_combo.addItem(voice.name)
        settings_layout.addWidget(self.voice_label)
        settings_layout.addWidget(self.voice_combo)
        
        # Speech rate
        self.rate_label = QLabel('Speech Rate:')
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(50, 300)
        self.rate_spin.setValue(150)
        self.rate_spin.setToolTip('Words per minute')
        settings_layout.addWidget(self.rate_label)
        settings_layout.addWidget(self.rate_spin)
        
        self.settings_panel.setLayout(settings_layout)
        self.settings_panel.hide()
        layout.addWidget(self.settings_panel)

        # Audio to Text button
        self.audio_text_btn = QPushButton('START Audio To Text')
        self.audio_text_btn.setToolTip('Convert speech to text (Ctrl+Shift+A)')
        self.audio_text_btn.clicked.connect(self.toggle_audio_to_text)
        layout.addWidget(self.audio_text_btn)
        
        # Text to Audio button
        self.text_audio_btn = QPushButton('START Text To Audio')
        self.text_audio_btn.setToolTip('Read selected text (Ctrl+Shift+S)')
        self.text_audio_btn.clicked.connect(self.toggle_text_to_audio)
        layout.addWidget(self.text_audio_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
        # Register global shortcuts
        keyboard.add_hotkey('ctrl+shift+a', self.toggle_audio_to_text)
        keyboard.add_hotkey('ctrl+shift+s', self.toggle_text_to_audio)
        logger.info("Keyboard shortcuts registered")

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip('Voice Controls')
        
        menu = QMenu()
        show_action = menu.addAction('Show')
        show_action.triggered.connect(self.show)
        quit_action = menu.addAction('Quit')
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def toggle_settings(self):
        if self.settings_panel.isHidden():
            self.settings_panel.show()
            self.settings_btn.setText('⚙️ Hide Settings')
        else:
            self.settings_panel.hide()
            self.settings_btn.setText('⚙️ Settings')
            self.save_settings()

    def save_settings(self):
        self.settings.setValue('voice', self.voice_combo.currentText())
        self.settings.setValue('rate', self.rate_spin.value())
        logger.info("Voice settings updated")

    def load_settings(self):
        voice = self.settings.value('voice', self.voice_combo.itemText(0))
        rate = self.settings.value('rate', 150)
        
        index = self.voice_combo.findText(voice)
        if index >= 0:
            self.voice_combo.setCurrentIndex(index)
        self.rate_spin.setValue(int(rate))

    def toggle_audio_to_text(self):
        if not self.transcription_thread or not self.transcription_thread.running:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        try:
            self.transcription_thread = TranscriptionThread()
            self.transcription_thread.finished.connect(self.on_transcription)
            self.transcription_thread.error.connect(self.on_error)
            self.transcription_thread.running = True
            self.transcription_thread.start()
            
            self.audio_text_btn.setText('STOP Audio To Text')
            self.audio_text_btn.setStyleSheet('background-color: #ff6b6b;')
            self.progress_bar.show()
            logger.info("Started speech recognition")
            
        except Exception as e:
            self.on_error(f"Failed to start listening: {str(e)}")

    def stop_listening(self):
        if self.transcription_thread:
            self.transcription_thread.stop()
            self.transcription_thread = None
            
        self.audio_text_btn.setText('START Audio To Text')
        self.audio_text_btn.setStyleSheet('')
        self.progress_bar.hide()
        logger.info("Stopped speech recognition")

    def toggle_text_to_audio(self):
        if not self.tts_thread or not self.tts_thread.isRunning():
            self.start_speaking()
        else:
            self.stop_speaking()

    def start_speaking(self):
        try:
            text = pyperclip.paste()
            if not text:
                raise Exception("No text selected")
                
            self.tts_thread = TTSThread(
                text,
                self.rate_spin.value(),
                self.voice_combo.currentText()
            )
            self.tts_thread.progress.connect(self.progress_bar.setValue)
            self.tts_thread.finished.connect(self.on_tts_finished)
            self.tts_thread.error.connect(self.on_error)
            self.tts_thread.start()
            
            self.text_audio_btn.setText('STOP Text To Audio')
            self.text_audio_btn.setStyleSheet('background-color: #ff6b6b;')
            self.progress_bar.show()
            
        except Exception as e:
            self.on_error(f"Failed to start speaking: {str(e)}")

    def stop_speaking(self):
        if self.tts_thread:
            self.tts_thread.stop()
            self.tts_thread = None
            
        self.text_audio_btn.setText('START Text To Audio')
        self.text_audio_btn.setStyleSheet('')
        self.progress_bar.hide()

    def on_transcription(self, text):
        if text:
            pyperclip.copy(text)
            keyboard.write(text)

    def on_tts_finished(self):
        self.stop_speaking()

    def on_error(self, error):
        logger.error(f"Listening error: {error}")
        if 'audio' in error.lower():
            self.stop_listening()
        elif 'speak' in error.lower():
            self.stop_speaking()

    def closeEvent(self, event):
        self.hide()
        event.ignore()  # Don't actually close, just hide
