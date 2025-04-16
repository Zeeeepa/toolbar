# Toolbar - Windows Text-to-Speech & Speech-to-Text Widget

A comprehensive Windows toolbar widget that provides text-to-speech (TTS) and speech-to-text functionality using local processing capabilities.

## Features

- Text-to-Speech (TTS) conversion
- Speech-to-Text transcription
- Voice activity detection
- Local processing (no cloud services required)
- Easy-to-use toolbar interface
- Customizable voice settings

## Requirements

- Python 3.8 or higher
- Windows operating system
- Audio input/output devices

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Zeeeepa/toolbar.git
cd toolbar
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows
```

3. Install the package and dependencies:
```bash
pip install -e .
```

## Usage

1. Start the toolbar:
```bash
start_toolbar
```

2. The toolbar will appear as a floating widget on your Windows desktop.

3. Features:
   - Click the microphone icon to toggle speech-to-text
   - Click the speaker icon to toggle text-to-speech
   - Use the settings icon to configure voice preferences

## Development Setup

1. Install development dependencies:
```bash
pip install -r requirements.txt
```

2. Install additional dependencies for voice features:
```bash
pip install pyttsx3 SpeechRecognition pyperclip pyautogui keyboard
```

## Project Structure

```
toolbar/
├── Widget/
│   ├── tts/            # Text-to-speech functionality
│   ├── utils/          # Utility functions and audio processing
│   └── voice/          # Speech-to-text functionality
├── requirements.txt    # Project dependencies
├── setup.py           # Package configuration
└── README.md          # Documentation
```

## Troubleshooting

1. Audio Device Issues:
   - Ensure your microphone is properly connected and set as the default input device
   - Check Windows sound settings for proper device configuration

2. Installation Issues:
   - Make sure you have Python 3.8+ installed
   - Update pip: `python -m pip install --upgrade pip`
   - Install Visual C++ build tools if required for Windows

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
