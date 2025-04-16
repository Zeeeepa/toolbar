import threading
import queue
import sounddevice as sd
import numpy as np
import vosk
import pyttsx3
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QThread

class VoiceRecognitionThread(QThread):
    text_received = pyqtSignal(str)
    
    def __init__(self, sample_rate=16000):
        super().__init__()
        self.sample_rate = sample_rate
        self.running = False
        self.q = queue.Queue()
        
        # Initialize Vosk model
        model = vosk.Model(lang="en-us")
        self.recognizer = vosk.KaldiRecognizer(model, self.sample_rate)
        
    def callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.q.put(bytes(indata))
        
    def run(self):
        self.running = True
        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000,
                             dtype="int16", channels=1, callback=self.callback):
            while self.running:
                data = self.q.get()
                if self.recognizer.AcceptWaveform(data):
                    result = self.recognizer.Result()
                    text = eval(result)["text"]
                    if text:
                        self.text_received.emit(text)
                        
    def stop(self):
        self.running = False

class VoiceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.init_tts()
        self.init_stt()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # TTS controls
        tts_layout = QHBoxLayout()
        self.play_btn = QPushButton("🔊 Read Selected")
        self.play_btn.clicked.connect(self.read_selected)
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.stop_reading)
        tts_layout.addWidget(self.play_btn)
        tts_layout.addWidget(self.stop_btn)
        
        # STT controls
        stt_layout = QHBoxLayout()
        self.record_btn = QPushButton("🎤 Start Dictation")
        self.record_btn.setCheckable(True)
        self.record_btn.clicked.connect(self.toggle_recording)
        stt_layout.addWidget(self.record_btn)
        
        layout.addLayout(tts_layout)
        layout.addLayout(stt_layout)
        self.setLayout(layout)
        
    def init_tts(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        
    def init_stt(self):
        self.stt_thread = VoiceRecognitionThread()
        self.stt_thread.text_received.connect(self.handle_recognized_text)
        
    def read_selected(self):
        # Get selected text from clipboard
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.engine.say(text)
            self.engine.runAndWait()
            
    def stop_reading(self):
        self.engine.stop()
        
    def toggle_recording(self, checked):
        if checked:
            self.record_btn.setText("⏺️ Stop Dictation")
            self.stt_thread.start()
        else:
            self.record_btn.setText("🎤 Start Dictation")
            self.stt_thread.stop()
            self.stt_thread.wait()
            
    def handle_recognized_text(self, text):
        # Insert recognized text at cursor position
        focused_widget = QApplication.focusWidget()
        if hasattr(focused_widget, 'insertPlainText'):
            focused_widget.insertPlainText(text + " ")
            
    def closeEvent(self, event):
        self.stt_thread.stop()
        self.stt_thread.wait()
        super().closeEvent(event)
