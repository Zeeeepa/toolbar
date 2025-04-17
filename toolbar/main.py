import sys
from PyQt6.QtWidgets import QApplication
from .voice.voice_plugin import VoicePlugin

def main():
    app = QApplication(sys.argv)
    widget = VoicePlugin()
    widget.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
