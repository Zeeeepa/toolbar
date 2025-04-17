import sys
import speech_recognition as sr
import pyttsx3
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt6.QtCore import QThread, pyqtSignal, Qt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('WidgetLogger')

class SpeechThread(QThread):
    """Thread for handling speech recognition."""
    text_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.running = False

    def run(self):
        try:
            with sr.Microphone() as source:
                logger.info("Started speech recognition")
                self.status_signal.emit("Listening...")
                self.recognizer.adjust_for_ambient_noise(source)
                logger.info("Adjusted for ambient noise")
                
                while self.running:
                    try:
                        audio = self.recognizer.listen(source, timeout=5)
                        text = self.recognizer.recognize_google(audio)
                        self.text_signal.emit(text)
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except Exception as e:
                        logger.error(f"Error in speech recognition: {str(e)}")
                        self.error_signal.emit(str(e))
                        break

        except Exception as e:
            logger.error(f"Error in microphone setup: {str(e)}")
            self.error_signal.emit(str(e))

        self.status_signal.emit("Stopped")
        logger.info("Stopped speech recognition")

class TTSThread(QThread):
    """Thread for handling text-to-speech."""
    error_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)

    def __init__(self, text):
        super().__init__()
        self.text = text
        self.engine = pyttsx3.init()

    def run(self):
        try:
            self.status_signal.emit("Speaking...")
            self.engine.say(self.text)
            self.engine.runAndWait()
            self.status_signal.emit("Stopped")
        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            self.error_signal.emit(str(e))

class VoicePlugin(QMainWindow):
    """Main window for the voice plugin."""
    def __init__(self):
        super().__init__()
        self.speech_thread = None
        self.tts_thread = None
        self.init_ui()
        logger.info("VoicePlugin initialized successfully")

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('Voice Controls')
        self.setGeometry(100, 100, 400, 500)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create settings button
        self.settings_btn = QPushButton('⚙️ Settings')
        layout.addWidget(self.settings_btn)

        # Create text area
        self.text_area = QTextEdit()
        layout.addWidget(self.text_area)

        # Create speech-to-text button
        self.stt_btn = QPushButton('START Audio To Text')
        self.stt_btn.clicked.connect(self.toggle_speech_recognition)
        layout.addWidget(self.stt_btn)

        # Create text-to-speech button
        self.tts_btn = QPushButton('START Text To Audio')
        self.tts_btn.clicked.connect(self.speak_text)
        layout.addWidget(self.tts_btn)

        # Create status label
        self.status_label = QLabel('Ready')
        layout.addWidget(self.status_label)

    def toggle_speech_recognition(self):
        """Toggle speech recognition on/off."""
        if self.speech_thread is None or not self.speech_thread.running:
            # Start speech recognition
            self.speech_thread = SpeechThread()
            self.speech_thread.text_signal.connect(self.update_text)
            self.speech_thread.error_signal.connect(self.handle_error)
            self.speech_thread.status_signal.connect(self.update_status)
            self.speech_thread.running = True
            self.speech_thread.start()
            self.stt_btn.setText('STOP Audio To Text')
        else:
            # Stop speech recognition
            self.speech_thread.running = False
            self.speech_thread = None
            self.stt_btn.setText('START Audio To Text')

    def speak_text(self):
        """Convert selected text to speech."""
        if self.tts_thread is None or not self.tts_thread.isRunning():
            # Start text-to-speech
            text = self.text_area.textCursor().selectedText()
            if not text:
                text = self.text_area.toPlainText()
            if text:
                self.tts_thread = TTSThread(text)
                self.tts_thread.error_signal.connect(self.handle_error)
                self.tts_thread.status_signal.connect(self.update_status)
                self.tts_thread.start()
                self.tts_btn.setText('STOP Text To Audio')
        else:
            # Stop text-to-speech
            self.tts_thread.terminate()
            self.tts_thread = None
            self.tts_btn.setText('START Text To Audio')

    def update_text(self, text):
        """Update the text area with recognized speech."""
        cursor = self.text_area.textCursor()
        cursor.insertText(text + " ")
        self.text_area.setTextCursor(cursor)

    def handle_error(self, error):
        """Handle errors from speech recognition or TTS."""
        self.status_label.setText(f"Error: {error}")
        logger.error(f"Error: {error}")

    def update_status(self, status):
        """Update the status label."""
        self.status_label.setText(status)

    def closeEvent(self, event):
        """Handle window close event."""
        if self.speech_thread and self.speech_thread.running:
            self.speech_thread.running = False
        if self.tts_thread and self.tts_thread.isRunning():
            self.tts_thread.terminate()
        super().closeEvent(event)
