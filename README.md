# Toolbar

A Windows toolbar application for text-to-speech and speech-to-text functionality.

## Features

- Text-to-Speech (TTS) conversion
- Speech-to-Text (STT) transcription
- Audio file processing and WebM encoding
- Voice activity detection
- Windows-style UI with minimalist design

## Installation

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/toolbar.git
cd toolbar

# Install the package
pip install -e .
```

## Usage

After installation, you can start the toolbar by running:

```bash
start_toolbar
```

This will launch the Windows toolbar interface with:
- A microphone button for speech recording
- A text input field for TTS
- Audio playback controls
- Settings panel for model configuration

## Development

The project structure:

```
toolbar/
├── widgets/
│   ├── audio/
│   │   ├── processor.py    # Audio processing utilities
│   │   ├── recorder.py     # Audio recording functionality
│   │   └── encoder.py      # WebM encoding implementation
│   ├── tts/
│   │   ├── engine.py       # TTS engine implementation
│   │   └── widget.py       # TTS UI component
│   └── stt/
│       ├── engine.py       # STT engine implementation
│       └── widget.py       # STT UI component
├── ui/
│   ├── main_window.py      # Main application window
│   └── toolbar.py          # Toolbar UI implementation
└── main.py                 # Application entry point
```

## Requirements

- Python 3.8 or higher
- PyQt6 for UI
- torch and torchaudio for audio processing
- transformers for TTS/STT models
- Additional dependencies listed in setup.py
