# Toolbar Plugin System

The Toolbar application uses a dynamic plugin system that automatically loads plugins from the plugins directory. This document explains how to create and configure plugins for the Toolbar application.

## Plugin Structure

A plugin is a directory in the `plugins` folder with the following structure:

```
plugins/
  my_plugin/
    __init__.py       # Required: Contains the plugin class
    metadata.json     # Optional: Contains plugin metadata
    other_files.py    # Optional: Additional plugin files
```

## Creating a Plugin

To create a plugin, follow these steps:

1. Create a new directory in the `plugins` folder with your plugin name
2. Create an `__init__.py` file that defines a class inheriting from `Plugin`
3. Optionally create a `metadata.json` file to define plugin metadata

### Plugin Class

Your plugin must define a class that inherits from `Plugin` in the `__init__.py` file:

```python
from Toolbar.core.plugin_system import Plugin

class MyPlugin(Plugin):
    def __init__(self):
        # Initialize your plugin
        pass
    
    def initialize(self, config):
        # Called when the plugin is loaded
        self.config = config
        # Initialize your plugin with the configuration
    
    def cleanup(self):
        # Called when the plugin is unloaded
        # Clean up resources
        pass
    
    def get_icon(self):
        # Return an icon for the plugin
        from PyQt5.QtGui import QIcon
        return QIcon.fromTheme("my-icon")
    
    def get_title(self):
        # Return a title for the plugin
        return "My Plugin"
    
    def activate(self):
        # Called when the plugin is activated
        # Show your plugin's UI or perform actions
        pass
    
    @property
    def name(self):
        return "My Plugin"
    
    @property
    def version(self):
        return "1.0.0"
    
    @property
    def description(self):
        return "My awesome plugin"
    
    @property
    def dependencies(self):
        # List of plugin names that this plugin depends on
        return []
```

### Plugin Metadata

You can define plugin metadata in a `metadata.json` file:

```json
{
    "name": "my_plugin",
    "display_name": "My Plugin",
    "version": "1.0.0",
    "description": "My awesome plugin",
    "author": "Your Name",
    "dependencies": ["other_plugin"],
    "priority": 0,
    "settings": {
        "enabled": true,
        "custom_setting": "default_value"
    }
}
```

The metadata file is optional, but it provides additional information about your plugin:

- `name`: The name of the plugin (should match the directory name)
- `display_name`: The display name of the plugin
- `version`: The version of the plugin
- `description`: A description of the plugin
- `author`: The author of the plugin
- `dependencies`: A list of plugin names that this plugin depends on
- `priority`: The loading priority of the plugin (higher values are loaded first)
- `settings`: Default settings for the plugin

## Plugin Dependencies

Plugins can depend on other plugins. The plugin system will ensure that plugins are loaded in the correct order based on their dependencies.

To define dependencies, either:

1. Add a `dependencies` list to your `metadata.json` file, or
2. Override the `dependencies` property in your plugin class

## Plugin Loading Order

Plugins are loaded in the following order:

1. Plugins with no dependencies
2. Plugins with dependencies, after their dependencies are loaded
3. Plugins with the same dependencies are loaded based on their priority (higher priority first)

## Example Plugin

See the `example_plugin` directory for a complete example of a plugin.

## Troubleshooting

If your plugin fails to load, check the application logs for error messages. Common issues include:

- Missing dependencies
- Syntax errors in the plugin code
- Missing required files
- Circular dependencies

## Plugin Settings

Plugins can define default settings in their `metadata.json` file. These settings can be accessed and modified through the plugin's configuration.

To access settings in your plugin:

```python
def initialize(self, config):
    self.config = config
    
    # Get a setting with a default value
    my_setting = self.config.get_setting("my_plugin.my_setting", "default_value")
    
    # Set a setting
    self.config.set_setting("my_plugin.my_setting", "new_value")
    
    # Save settings
    self.config.save()
```

## Plugin UI

Plugins can provide a UI that is shown when the plugin is activated. To create a UI, override the `activate` method:

```python
def activate(self):
    # Create and show your UI
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
    
    widget = QWidget()
    widget.setWindowTitle("My Plugin")
    
    layout = QVBoxLayout(widget)
    layout.addWidget(QLabel("Hello from My Plugin!"))
    
    widget.show()
    widget.raise_()
```
