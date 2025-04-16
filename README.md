# Toolbar - Taskbar Application

A modular taskbar application with plugin support and audio processing capabilities, built with Python and PyQt5.

## Features

- **Taskbar Interface**: Sits at the bottom of the screen like a traditional taskbar
- **Application Launcher**: Launch your favorite applications with a single click
- **Plugin System**: Extend functionality with custom plugins
- **System Tray Integration**: Access the application from the system tray
- **Start Menu**: Access applications and settings from a start menu
- **Audio Processing**: Built-in audio recording, encoding, and processing capabilities
- **Voice Plugins**: Text-to-speech and speech recognition support
- **Customizable**: Configure the appearance and behavior to your liking
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Audio dependencies (automatically installed):
  - pyttsx3 (text-to-speech)
  - SpeechRecognition (speech recognition)
  - webm-muxer (audio encoding)
  - sounddevice (audio capture)
  - numpy (audio processing)

### Option 1: Install with pip

The easiest way to install Toolbar is using pip:

```bash
# Install directly from the repository
pip install git+https://github.com/Zeeeepa/toolbar.git

# Or install in development mode
pip install -e .
```

After installation, you can start the application by running:

```bash
toolbar
```

### Option 2: Install from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/Zeeeepa/toolbar.git
   cd toolbar
   ```

2. Install the package:
   ```bash
   pip install -e .
   ```

   This will install the toolbar and its dependencies in development mode.

### Option 3: Run Without Installing

If you prefer to run the application without installing it, you can run the main module directly:

```bash
python -m Toolbar.main
```

## Usage

### Starting the Application

After installation, you can start the application in several ways:

- Run the `toolbar` command in your terminal
- Run `python -m Toolbar.main`

### Interface

The taskbar interface consists of several components:

- **Start Button**: Click to open the start menu
- **Application Buttons**: Click to launch applications
- **System Tray Icon**: Access the application from the system tray
- **Clock**: Displays the current time
- **Audio Controls**: Access audio recording and processing features

### Audio Processing Features

The toolbar includes comprehensive audio processing capabilities:

1. **Audio Recording**:
   - Click the microphone icon to start recording
   - Supports various audio formats and quality settings
   - Real-time audio visualization

2. **Audio Encoding**:
   - WebM audio encoding support
   - Configurable bitrate and quality settings
   - Multiple channel support

3. **Audio Processing**:
   - Slice and trim audio files
   - Convert between formats
   - Apply audio effects and filters

4. **Voice Features**:
   - Text-to-speech capabilities
   - Speech recognition
   - Voice command support

Example audio processing code:
```python
from toolbar.audio import AudioProcessor

# Initialize audio processor
processor = AudioProcessor()

# Start recording
processor.start_recording()

# Stop and save recording
audio_data = processor.stop_recording()

# Process audio
processed_audio = processor.process_audio(audio_data, {
    'format': 'webm',
    'codec': 'opus',
    'bitrate': 96000,
    'channels': 2
})

# Save to file
processor.save_audio(processed_audio, 'output.webm')
```

### Adding Applications

You can add applications to the taskbar in several ways:

1. From the start menu:
   - Click the start button
   - Right-click on an application
   - Select "Pin to Taskbar"

2. Drag and drop:
   - Drag an application from your file explorer
   - Drop it onto the taskbar

3. From the settings:
   - Open the settings dialog
   - Go to the "Applications" tab
   - Click "Add Application"
   - Select the application executable

### Plugins

The toolbar supports plugins to extend its functionality. Several plugins are included:

- **GitHub Plugin**: Integrates with GitHub repositories
- **Linear Plugin**: Integrates with Linear issue tracking
- **Template Prompt Plugin**: Manages template prompts
- **Auto Scripting Plugin**: Automates tasks
- **Events Plugin**: Manages event-driven workflows

#### Creating Plugins

You can create your own plugins by implementing the `Plugin` interface:

```python
from Toolbar.core.plugin_system import Plugin

class MyPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.dialog = None
    
    def initialize(self, config):
        self.config = config
        # Initialize your plugin
    
    def cleanup(self):
        # Clean up resources
    
    def get_icon(self):
        # Return an icon for the taskbar button
        from PyQt5.QtGui import QIcon
        return QIcon.fromTheme("my-icon")
    
    def get_title(self):
        # Return a title for the taskbar button
        return "My Plugin"
    
    def activate(self):
        # Called when the taskbar button is clicked
        # Show your plugin's UI
    
    @property
    def name(self):
        return "MyPlugin"
    
    @property
    def version(self):
        return "1.0.0"
    
    @property
    def description(self):
        return "My custom plugin"
```

Place your plugin in a subdirectory of the `Toolbar/plugins` directory or in a custom plugin directory specified in the configuration.

## Configuration

The toolbar configuration is stored in a JSON file in the user's configuration directory:

- Windows: `%APPDATA%\toolbar\config.json`
- macOS: `~/Library/Application Support/toolbar/config.json`
- Linux: `~/.config/toolbar/config.json`

You can modify the configuration directly or through the settings dialog in the application.

## Development

### Project Structure

```
toolbar/
├── __init__.py             # Root package
├── setup.py                # Package setup
├── Toolbar/                # Main package
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── core/               # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py       # Configuration management
│   │   ├── plugin_system.py  # Plugin system
│   │   └── enhanced_plugin_system.py  # Enhanced plugin system
│   ├── main.py             # Entry point
│   ├── plugins/            # Plugins
│   │   ├── __init__.py
│   │   ├── github/         # GitHub plugin
│   │   ├── linear/         # Linear plugin
│   │   ├── templateprompt/ # Template prompt plugin
│   │   ├── autoscripting/  # Auto scripting plugin
│   │   └── events/         # Events plugin
│   └── ui/                 # User interface
│       ├── __init__.py
│       ├── notification_widget.py
│       ├── toolbar_settings.py
│       └── toolbar_ui.py   # Main UI
```

### Building

To build a distributable package:

```bash
python -m pip install build
python -m build
```

This will create a wheel file in the `dist` directory that can be installed with pip.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - Qt bindings for Python
- [appdirs](https://github.com/ActiveState/appdirs) - Platform-specific directory paths
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment variable management
