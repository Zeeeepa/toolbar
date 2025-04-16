from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import sys
from .tts.tts_plugin import TTSPlugin
from .voice.voice_plugin import VoicePlugin

def main():
    app = QApplication(sys.argv)
    
    # Create TTS and Voice plugins
    tts_plugin = TTSPlugin()
    voice_plugin = VoicePlugin()
    
    # Show the plugins
    tts_plugin.show()
    voice_plugin.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
