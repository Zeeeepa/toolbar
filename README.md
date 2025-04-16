# Toolbar

A PyQt6-based toolbar application with plugin support for audio processing and GitHub integration.

## Features

- Plugin-based architecture
- Audio processing capabilities
- GitHub integration
- Event handling

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Zeeeepa/toolbar.git
cd toolbar
```

2. Install the package:
```bash
pip install -e .
```

## Usage

Run the toolbar:
```bash
start_toolbar
```

## Audio Processing

The toolbar includes audio processing capabilities:
- WebM audio encoding
- Audio buffer handling
- Audio slicing and processing
- Support for multiple audio channels

## Plugins

### Events Plugin
Handles various events and provides a widget interface.

### GitHub Plugin
Integrates with GitHub and provides a dialog interface for GitHub Actions.

## Development

To add a new plugin:

1. Create a new directory in `Toolbar/plugins/`
2. Create a `plugin.py` file with your plugin class
3. Implement the required interface methods

Example plugin structure:
```python
class MyPlugin:
    def __init__(self):
        self.name = "my_plugin"
        self.widget = None
        
    def get_widget(self):
        # Return your plugin's widget
        pass
```

## License

MIT
