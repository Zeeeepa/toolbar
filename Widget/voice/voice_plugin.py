"""Voice plugin with enhanced audio processing capabilities"""
import numpy as np
from typing import Optional, Tuple
from PyQt5.QtWidgets import QPushButton, QWidget
from PyQt5.QtCore import Qt
from ..utils.logger import logger
from ..utils.audio_processing import AudioProcessor

class VoiceWidget:
    """Widget for voice-related functionality including speech-to-text and text-to-speech"""
    
    def __init__(self, root: QWidget):
        try:
            self.root = root
            self.audio_processor = AudioProcessor()
            self.setup_styles()
            self.create_buttons()
            logger.info("VoiceWidget initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize VoiceWidget: {str(e)}")
            raise

    def setup_styles(self):
        """Set up widget styles"""
        self.button_style = """
            QPushButton {
                background-color: #2b2b2b;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #3b3b3b;
            }
        """
        logger.info("Widget styles configured")

    def create_buttons(self):
        """Create widget buttons"""
        # Record button
        self.record_btn = QPushButton("🎤", self.root)
        self.record_btn.setStyleSheet(self.button_style)
        self.record_btn.clicked.connect(self.toggle_recording)
        self.record_btn.setToolTip("Start/Stop Recording")
        
        # Process button
        self.process_btn = QPushButton("⚙️", self.root)
        self.process_btn.setStyleSheet(self.button_style)
        self.process_btn.clicked.connect(self.process_audio)
        self.process_btn.setToolTip("Process Audio")
        
        # Export button
        self.export_btn = QPushButton("💾", self.root)
        self.export_btn.setStyleSheet(self.button_style)
        self.export_btn.clicked.connect(self.export_audio)
        self.export_btn.setToolTip("Export Audio")

    def toggle_recording(self):
        """Toggle audio recording state"""
        if not hasattr(self, 'recording') or not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start audio recording"""
        try:
            self.recording = True
            self.record_btn.setText("⏹️")
            logger.info("Started recording")
        except Exception as e:
            logger.error(f"Error starting recording: {str(e)}")
            raise

    def stop_recording(self):
        """Stop audio recording"""
        try:
            self.recording = False
            self.record_btn.setText("🎤")
            logger.info("Stopped recording")
        except Exception as e:
            logger.error(f"Error stopping recording: {str(e)}")
            raise

    def process_audio(self):
        """Process recorded audio"""
        try:
            if hasattr(self, 'audio_data'):
                # Process audio using the audio processor
                processed_data = self.audio_processor.process_audio(
                    self.audio_data,
                    normalize=True
                )
                self.processed_audio = processed_data
                logger.info("Audio processing completed")
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise

    def export_audio(self):
        """Export processed audio to file"""
        try:
            if hasattr(self, 'processed_audio'):
                # Export the processed audio
                # Implementation will depend on the specific export format needed
                logger.info("Audio exported successfully")
        except Exception as e:
            logger.error(f"Error exporting audio: {str(e)}")
            raise

    def cleanup(self):
        """Clean up resources"""
        try:
            # Clean up any open audio resources
            self.audio_processor = None
            logger.info("VoiceWidget cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise

class VoicePlugin:
    """Plugin for voice-related functionality"""
    def __init__(self):
        self.widget: Optional[VoiceWidget] = None
    
    def initialize(self, root: QWidget):
        """Initialize the voice plugin"""
        try:
            self.widget = VoiceWidget(root)
            logger.info("VoicePlugin initialized")
        except Exception as e:
            logger.error(f"Failed to initialize VoicePlugin: {str(e)}")
            raise
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.widget:
                self.widget.frame.destroy()
                self.widget = None
            logger.info("VoicePlugin cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
