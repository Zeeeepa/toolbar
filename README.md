# Toolbar

A modular, plugin-based toolbar application for developers.

## Features

- Modular plugin-based architecture
- GitHub integration for repository monitoring and notifications
- Linear issue tracking integration
- Automation tools for common development tasks
- Customizable UI with dockable widgets
- Cross-platform support (Windows, macOS, Linux)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Install from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/Zeeeepa/toolkit.git
   cd toolkit
   ```

2. Install the package and dependencies:
   ```bash
   pip install -e .
   ```

   This will install the Toolbar application in development mode, along with all required dependencies.

### Install Dependencies Only

If you prefer not to install the package, you can just install the dependencies:

```bash
pip install -r Toolbar/requirements.txt
```

## Usage

### Running the Application

After installation, you can run the toolbar using:

```bash
toolbar
```

Or, if you didn't install the package:

```bash
python run_toolbar.py
```

### Configuration

The application stores its configuration in a JSON file located at:
- Windows: `%APPDATA%\Toolbar\config.json`
- macOS: `~/Library/Application Support/Toolbar/config.json`
- Linux: `~/.config/Toolbar/config.json`

## Plugin System

The Toolbar application uses a modular plugin system that allows for easy extension of functionality.

### Available Plugins

- **GitHub Integration**: Monitor repositories, receive notifications, and manage issues
- **Linear Integration**: Create and track issues in Linear
- **Automation Manager**: Run custom scripts and automate repetitive tasks

### Creating Custom Plugins

To create a custom plugin:

1. Create a new directory in the `Toolbar/plugins` directory
2. Create an `__init__.py` file that defines a class inheriting from `Toolbar.core.plugin_system.Plugin`
3. Implement the required methods: `initialize`, `cleanup`, `name`, `version`, and `description`

Example:

```python
from Toolbar.core.plugin_system import Plugin

class MyCustomPlugin(Plugin):
    def initialize(self, config):
        # Initialize your plugin
        pass
        
    def cleanup(self):
        # Clean up resources
        pass
        
    @property
    def name(self):
        return "My Custom Plugin"
        
    @property
    def version(self):
        return "1.0.0"
        
    @property
    def description(self):
        return "A custom plugin for the Toolbar application"
```

## Development

### Project Structure

```
toolkit/
├── Toolbar/
│   ├── core/               # Core functionality
│   │   ├── config.py       # Configuration management
│   │   ├── github/         # GitHub core functionality
│   │   ├── plugin_system/  # Plugin system
│   │   └── ...
│   ├── plugins/            # Plugin modules
│   │   ├── github/         # GitHub plugin
│   │   ├── linear/         # Linear plugin
│   │   ├── automationmanager/ # Automation plugin
│   │   └── ...
│   ├── ui/                 # UI components
│   │   ├── github_ui.py    # GitHub UI components
│   │   └── ...
│   └── main.py             # Application entry point
├── run_toolbar.py          # Convenience script to run the application
├── setup.py                # Package setup script
└── README.md               # This file
```

### Building from Source

To build a distributable package:

```bash
python setup.py sdist bdist_wheel
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
