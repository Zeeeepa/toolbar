# Events Plugin

The Events plugin provides a visual node-based flow editor for creating event-driven automations in the Toolbar application. It serves as a central hub for connecting different plugins and automating workflows based on events from GitHub, Linear, and other services.

## Features

- Visual node-based flow editor for creating automations
- Support for various event triggers (GitHub, Linear, etc.)
- Conditional logic for event processing
- Action nodes for responding to events
- Integration with other plugins (GitHub, Linear, etc.)
- Event history and monitoring
- Customizable event templates

## Installation

1. Ensure the Events plugin is installed in your Toolbar application
2. For full functionality, install the following plugins:
   - GitHub plugin (for GitHub event triggers)
   - Linear plugin (for Linear event triggers)
   - Template Prompt plugin (for prompt templates)
   - Auto Scripting plugin (for custom scripts)

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
- Linear issue creation/updates/closure
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

### GitHub Plugin Integration

The Events plugin connects to the GitHub plugin to:
- Receive notifications about new PRs, branches, and repository updates
- Trigger workflows based on GitHub events
- Perform actions like auto-merging PRs

Example: Auto-merge PRs that only modify documentation files:
```
Trigger: GitHub PR Created
Condition: PR files contain only .md files
Action: Auto-merge PR
```

### Linear Plugin Integration

The Events plugin connects to the Linear plugin to:
- Receive notifications about new issues, updates, and closures
- Create Linear issues in response to events
- Update Linear issues based on conditions

Example: Create a Linear issue when a new branch is created:
```
Trigger: GitHub Branch Created
Action: Create Linear issue with title "Review branch: {branch.name}"
```

### Template Prompt Plugin Integration

The Events plugin uses the Template Prompt plugin to:
- Create dynamic prompts based on event data
- Use templates for consistent messaging
- Send prompts to various destinations

Example: Send a prompt when a PR is created:
```
Trigger: GitHub PR Created
Action: Send prompt using template "PR Review Request" to coordinates
```

### Auto Scripting Plugin Integration

The Events plugin uses the Auto Scripting plugin to:
- Run custom scripts in response to events
- Perform complex actions not covered by built-in actions
- Integrate with external systems

Example: Run a custom script when a Linear issue is closed:
```
Trigger: Linear Issue Closed
Action: Run script "update-dashboard.js"
```

## Configuration

The Events plugin can be configured through the Settings tab in the Events dialog:

- Enable/disable specific event triggers
- Configure integration with other plugins
- Set default behaviors for event processing
- Define global event templates

## Advanced Usage

### Creating Complex Workflows

You can create complex workflows by connecting multiple nodes:

1. Start with a trigger node (e.g., GitHub PR Created)
2. Add condition nodes to filter events (e.g., PR contains specific files)
3. Connect to action nodes for different outcomes (e.g., Auto-merge or Create Linear issue)
4. Add branching logic for different scenarios

### Using Event Templates

Save common event configurations as templates:

1. Create and configure an event
2. Click "Save as Template"
3. Give the template a name
4. Use the template when creating new events

### Event Monitoring

Monitor event processing and execution:

1. Open the Events dialog
2. Switch to the History tab
3. View all triggered events and their outcomes
4. Filter by event type, status, or date range

## Troubleshooting

### Common Issues

- **Events not triggering**: Ensure the corresponding plugin (GitHub/Linear) is properly configured
- **Actions not executing**: Check action parameters and permissions
- **Node connections not working**: Verify that nodes are properly connected in the flow editor

### Logging

The Events plugin logs all activity to the Toolbar log file. To view logs:

1. Open the Toolbar settings
2. Go to the Logs tab
3. Filter for "Events" to see Events plugin logs

## API Reference

The Events plugin provides a Python API for programmatic access:

```python
from Toolbar.plugins.events.core.event_system import EventManager, EventType, ActionType

# Get the event manager
event_manager = get_plugin_instance("Events").event_manager

# Create a new event
event = Event(
    id=str(uuid.uuid4()),
    name="My Custom Event",
    description="A custom event created via API",
    trigger=EventTrigger(
        id=str(uuid.uuid4()),
        name="Custom Trigger",
        event_type=EventType.GITHUB_PR_CREATED,
        conditions=[
            Condition(field="pull_request.title", operator="contains", value="feature")
        ]
    ),
    actions=[
        Action(
            id=str(uuid.uuid4()),
            name="Create Linear Issue",
            action_type=ActionType.CREATE_LINEAR_ISSUE,
            parameters=[
                ActionParameter(name="title_template", value="Review PR: {pull_request.title}"),
                ActionParameter(name="description_template", value="PR URL: {pull_request.html_url}")
            ]
        )
    ]
)

# Add the event
event_manager.add_event(event)
```
