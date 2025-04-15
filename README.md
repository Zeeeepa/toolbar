# Toolkit - Taskbar Application

A modular taskbar application with plugin support, built with Python and PyQt5.

## Features

- **Taskbar Interface**: Sits at the bottom of the screen like a traditional taskbar
- **Application Launcher**: Launch your favorite applications with a single click
- **Plugin System**: Extend functionality with custom plugins
- **System Tray Integration**: Access the application from the system tray
- **Start Menu**: Access applications and settings from a start menu
- **Customizable**: Configure the appearance and behavior to your liking
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Option 1: Install from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/Zeeeepa/toolkit.git
   cd toolkit
   ```

2. Install the package:
   ```bash
   python install_toolkit.py
   ```

   This will install the toolkit and its dependencies, create a desktop shortcut, and set up autostart.

   Additional options:
   - `--dev`: Install in development mode
   - `--no-shortcut`: Skip desktop shortcut creation
   - `--no-autostart`: Skip autostart setup

### Option 2: Run Without Installing

If you prefer to run the application without installing it, you can use the provided run script:

```bash
python run_toolkit.py
```

## Usage

### Starting the Application

After installation, you can start the application in several ways:

- Run the `toolbar` command in your terminal
- Use the desktop shortcut created during installation
- Run `python -m toolkit.toolbar.main`
- Use the run script: `python run_toolkit.py`

### Interface

The taskbar interface consists of several components:

- **Start Button**: Click to open the start menu
- **Application Buttons**: Click to launch applications
- **System Tray Icon**: Access the application from the system tray
- **Clock**: Displays the current time

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

The toolkit supports plugins to extend its functionality. Several plugins are included:

- **Example Plugin**: Demonstrates the plugin system
- **GitHub Plugin**: Integrates with GitHub repositories
- **Linear Plugin**: Integrates with Linear issue tracking

#### Creating Plugins

You can create your own plugins by implementing the `Plugin` interface:

```python
from toolkit.toolbar.core.plugin_system import Plugin

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

Place your plugin in a subdirectory of the `toolkit/toolbar/plugins` directory or in a custom plugin directory specified in the configuration.

## Configuration

The toolkit configuration is stored in a JSON file in the user's configuration directory:

- Windows: `%APPDATA%\toolkit\config.json`
- macOS: `~/Library/Application Support/toolkit/config.json`
- Linux: `~/.config/toolkit/config.json`

You can modify the configuration directly or through the settings dialog in the application.

## Development

### Project Structure

```
toolkit/
├── install_toolkit.py      # Installation script
├── run_toolkit.py          # Run script
├── setup.py                # Package setup
├── toolkit/                # Main package
│   ├── __init__.py
│   └── toolbar/            # Toolbar package
│       ├── __init__.py
│       ├── core/           # Core functionality
│       │   ├── __init__.py
│       │   ├── config.py   # Configuration management
│       │   └── plugin_system.py  # Plugin system
│       ├── main.py         # Entry point
│       ├── plugins/        # Plugins
│       │   ├── __init__.py
│       │   └── example/    # Example plugin
│       │       └── __init__.py
│       └── ui/             # User interface
│           ├── __init__.py
│           ├── notification_widget.py
│           ├── toolbar_settings.py
│           └── toolbar_ui.py  # Main UI
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
