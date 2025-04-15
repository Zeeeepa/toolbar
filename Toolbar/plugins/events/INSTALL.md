# Events Plugin Installation Guide

This guide will help you install and configure the Events plugin for the Toolbar application.

## Prerequisites

Before installing the Events plugin, ensure you have the following:

- Toolbar application installed (version 1.0.0 or higher)
- Python 3.7 or higher
- pip package manager
- Node.js and npm (optional, for development)

## Installation Methods

### Method 1: Using the Toolbar Plugin Manager (Recommended)

1. Open the Toolbar application
2. Go to Settings > Plugins
3. Click "Install Plugin"
4. Select "Events" from the available plugins
5. Click "Install"
6. Restart the Toolbar application

### Method 2: Manual Installation

1. Download the Events plugin from the [GitHub repository](https://github.com/Zeeeepa/toolbar)
2. Extract the plugin files to the Toolbar plugins directory:
   ```
   <toolbar_installation_path>/Toolbar/plugins/events/
   ```
3. Install the required dependencies:
   ```
   cd <toolbar_installation_path>/Toolbar/plugins/events/
   pip install -r requirements.txt
   ```
4. Restart the Toolbar application

### Method 3: Using npm (For Developers)

1. Clone the Toolbar repository:
   ```
   git clone https://github.com/Zeeeepa/toolbar.git
   ```
2. Navigate to the Events plugin directory:
   ```
   cd toolbar/Toolbar/plugins/events/
   ```
3. Install the plugin using npm:
   ```
   npm install
   ```
4. Link the plugin to your Toolbar installation:
   ```
   npm link
   cd <toolbar_installation_path>/Toolbar/plugins/
   npm link toolbar-events-plugin
   ```
5. Restart the Toolbar application

## Configuration

After installation, you need to configure the Events plugin:

1. Open the Toolbar application
2. Click on the Events button in the toolbar
3. Go to the Settings tab
4. Configure the following settings:
   - GitHub integration settings
   - Linear integration settings
   - Event history settings
5. Click "Save" to apply the settings

## Verifying Installation

To verify that the Events plugin is installed correctly:

1. Open the Toolbar application
2. Click on the Events button in the toolbar
3. The Events dialog should open
4. Create a new event to test the functionality

## Troubleshooting

If you encounter issues during installation:

1. Check the Toolbar logs for error messages
2. Ensure all dependencies are installed correctly
3. Verify that the plugin files are in the correct directory
4. Check that the plugin is enabled in the Toolbar settings

## Additional Resources

- [Events Plugin Documentation](https://github.com/Zeeeepa/toolbar/tree/main/Toolbar/plugins/events)
- [Toolbar Documentation](https://github.com/Zeeeepa/toolbar)
- [GitHub Repository](https://github.com/Zeeeepa/toolbar)

## Support

If you need help with the Events plugin, please:

1. Check the [GitHub Issues](https://github.com/Zeeeepa/toolbar/issues) for known problems
2. Create a new issue if your problem is not already reported
3. Contact the Toolbar support team for assistance
