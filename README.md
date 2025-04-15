# Toolbar

A customizable toolbar application for running scripts and integrating with GitHub and Linear.

## Features

- Run scripts with a single click
- Monitor GitHub repositories and notifications
- Integrate with Linear for issue tracking
- Customizable UI with various settings
- Plugin-based architecture for extensibility

## Installation

### Prerequisites

- Python 3.6 or higher
- PyQt5
- Required Python packages (see requirements.txt)

### Install from Source

1. Clone the repository:
   ```
   git clone https://github.com/Zeeeepa/toolkit.git
   cd toolkit
   ```

2. Install the required dependencies:
   ```
   pip install -r Toolbar/requirements.txt
   ```

3. Install the package:
   ```
   pip install -e .
   ```

## Usage

### Running the Toolbar

You can run the toolbar using the provided script:

```
python run_toolbar.py
```

Or, if you installed the package:

```
toolbar
```

### Adding Scripts

1. Click the "Add Script" button on the toolbar
2. Select a script file from your computer
3. Enter a name for the script
4. The script will be added to the toolbar

### GitHub Integration

1. Click the GitHub button on the toolbar
2. Enter your GitHub token in the settings dialog
3. Configure webhook settings if needed
4. Pin repositories to monitor

### Linear Integration

1. Click the Linear button on the toolbar
2. Enter your Linear API key in the settings dialog
3. Configure issue tracking settings

## Configuration

The toolbar can be configured through the settings dialog or by editing the configuration file directly.

### UI Settings

- Position: Top, bottom, left, or right
- Opacity: Adjust the transparency of the toolbar
- Stay on top: Keep the toolbar above other windows

### Script Settings

- Editor: Choose the editor to use for editing scripts
- Scripts folder: Set the folder where scripts are stored

## Plugin Development

The toolbar uses a plugin-based architecture, making it easy to extend its functionality.

### Creating a Plugin

1. Create a new folder in the `Toolbar/plugins` directory
2. Create an `__init__.py` file with a class that inherits from `Plugin`
3. Implement the required methods: `initialize`, `cleanup`, `name`, `version`, and `description`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- PyQt5 for the UI framework
- GitHub and Linear for their APIs
