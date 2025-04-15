# Toolkit

A modular toolkit application with plugin support for GitHub and Linear integration.

## Features

- Modular plugin system
- GitHub integration
- Linear integration
- Customizable UI
- Cross-platform support

## Installation

### Prerequisites

- Python 3.8 or higher
- PyQt5
- Git

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/Zeeeepa/toolkit.git
   cd toolkit
   ```

2. Install the package:
   ```bash
   python install_toolkit.py
   ```

   Or manually:
   ```bash
   pip install -e .
   ```

## Usage

### Running the Application

After installation, you can run the application using:

```bash
toolbar
```

Or using the run script:

```bash
python run_toolkit.py
```

### Configuration

The application stores its configuration in `~/.config/toolkit/config.json`. You can modify this file directly or use the settings dialog in the application.

## Plugin Development

### Creating a Plugin

1. Create a new directory in `toolkit/toolbar/plugins` with your plugin name.
2. Create an `__init__.py` file in your plugin directory.
3. Create a class that inherits from `Plugin` in the `__init__.py` file.
4. Implement the required methods.

Example:

```python
from toolkit.toolbar.core.plugin_system import Plugin

class MyPlugin(Plugin):
    def __init__(self):
        super().__init__()
    
    def initialize(self, config):
        # Initialize your plugin
        pass
    
    def cleanup(self):
        # Clean up resources
        pass
    
    @property
    def name(self):
        return "MyPlugin"
    
    @property
    def version(self):
        return "1.0.0"
    
    @property
    def description(self):
        return "My awesome plugin"
```

### Plugin UI

If your plugin has a UI, you can implement a `get_ui` method that returns a UI object. The UI object should have a `get_widget` method that returns a QWidget.

Example:

```python
def get_ui(self):
    return MyPluginUI()

class MyPluginUI:
    def __init__(self):
        self.widget = QWidget()
        # Initialize your UI
    
    def get_widget(self):
        return self.widget
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
