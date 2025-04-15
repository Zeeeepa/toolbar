# Events Plugin

The Events plugin provides a visual node-based flow editor for creating event-driven automations in the Toolbar application.

## Features

- Visual node-based flow editor for creating automations
- Support for various event triggers (GitHub, Linear, etc.)
- Conditional logic for event processing
- Action nodes for responding to events
- Integration with other plugins (GitHub, Linear, etc.)

## Usage

1. Click on the Events button in the toolbar to open the Events dialog
2. Create a new event in the Events tab
3. Switch to the Flow Editor tab to design your automation flow
4. Add trigger, action, and condition nodes
5. Connect the nodes to create your automation flow
6. Save the flow to apply it to the selected event

## Node Types

### Trigger Nodes

Trigger nodes represent the starting point of an automation flow. They are triggered by specific events such as:

- GitHub PR creation
- GitHub branch creation
- Linear issue creation
- Custom events

### Action Nodes

Action nodes represent actions to be performed when an event is triggered. Available actions include:

- Send a prompt to a specific location
- Create a Linear issue
- Auto-merge a PR
- Run a custom script

### Condition Nodes

Condition nodes allow for conditional logic in the automation flow. They can check various conditions such as:

- PR file types
- PR title/description content
- Branch name patterns
- Issue labels/status

## Integration with Other Plugins

The Events plugin integrates with other plugins to provide a comprehensive automation solution:

- **GitHub Plugin**: Trigger events on PR creation, branch creation, etc.
- **Linear Plugin**: Trigger events on issue creation, update, etc.
- **Template Prompt Plugin**: Use templates for sending prompts
- **Auto Scripting Plugin**: Run custom scripts in response to events

## Configuration

The Events plugin can be configured through the Settings tab in the Events dialog:

- Enable/disable specific event triggers
- Configure integration with other plugins
- Set default behaviors for event processing
