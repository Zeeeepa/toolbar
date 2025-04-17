from PyQt6.QtWidgets import QApplication
import sys
from .voice.voice_plugin import VoicePlugin

def main():
    app = QApplication(sys.argv)
    voice_plugin = VoicePlugin()
    voice_plugin.show()
    return app.exec()

if __name__ == "__main__":
    main()
