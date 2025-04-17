from PyQt6.QtWidgets import QApplication
from .voice.voice_plugin import VoicePlugin

def main():
    """Main entry point for the toolbar application."""
    app = QApplication([])
    
    # Initialize the voice plugin with unified interface
    voice_plugin = VoicePlugin()
    voice_plugin.show()
    
    return app.exec()

if __name__ == "__main__":
    main()
