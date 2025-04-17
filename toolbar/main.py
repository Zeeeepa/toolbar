import sys
import logging
from PyQt6.QtWidgets import QApplication
from .voice.voice_plugin import VoicePlugin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('WidgetLogger')

def main():
    app = QApplication(sys.argv)
    
    # Create and show the voice plugin
    voice_plugin = VoicePlugin()
    voice_plugin.show()
    
    return app.exec()

if __name__ == "__main__":
    main()
