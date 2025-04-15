# Enhanced Events Plugin

This is an enhancement to the existing Events plugin, adding improved node flow editor functionality for creating event-driven automations in the Toolbar application.

## Enhanced Features

- **Improved Node Flow Editor**
  - Better visual feedback for nodes and connections
  - Grid background for easier node placement
  - Zoom controls for better navigation
  - Node palette for easy node creation
  - Color-coded connections for success/failure paths

- **Enhanced Node Types**
  - Improved event nodes with better visual feedback
  - Enhanced condition nodes with success/failure outputs
  - Improved action nodes with better parameter handling
  - Better integration with other plugins

- **UI Improvements**
  - Enhanced node editor dialog with better layout
  - Node palette for easy node creation
  - Better visual feedback for node states
  - Improved connection handling

## Installation

1. Ensure the Events plugin is installed in your Toolbar application
2. The enhanced node flow editor is automatically available in the Events dialog

## Usage

1. Click on the Events button in the toolbar to open the Events dialog
2. Click on the "Enhanced Flow Editor" button to open the enhanced node flow editor
3. Use the node palette to add nodes to the scene
4. Connect nodes by dragging from output sockets to input sockets
5. Configure nodes by double-clicking on them
6. Save the flow to apply it to the selected event

## Node Types

### Event Nodes

Event nodes represent the starting point of an automation flow. They are triggered by specific events such as:

- GitHub PR creation
- GitHub branch creation
- Linear issue creation/updates/closure
- Custom events

### Condition Nodes

Condition nodes allow you to add conditional logic to your automation flow. They have:

- One input socket
- Two output sockets (success and failure)
- Configurable condition properties (field, operator, value)

### Action Nodes

Action nodes represent actions to be performed when an event is triggered. Available actions include:

- Send a prompt to a specific location
- Create a Linear issue
- Auto-merge a PR
- Run a custom script

## Integration with Other Plugins

The enhanced node flow editor integrates with other plugins:

- **GitHub Plugin**: Trigger events on PR creation, branch creation, etc.
- **Linear Plugin**: Trigger events on issue creation, updates, etc.
- **Template Prompt Plugin**: Use prompt templates in action nodes
- **Auto Scripting Plugin**: Run custom scripts in action nodes

## Customization

The enhanced node flow editor can be customized in several ways:

- Node colors can be changed by modifying the brush colors
- Grid size and color can be adjusted
- Zoom levels can be configured
- Node palette can be extended with custom node types
