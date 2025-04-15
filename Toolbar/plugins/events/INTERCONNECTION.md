# Events Plugin Interconnection Guide

This guide explains how the Events plugin connects with other plugins in the Toolbar ecosystem to create a comprehensive automation solution.

## Plugin Interconnection Architecture

The Events plugin serves as a central hub for connecting different plugins and automating workflows. It uses a modular architecture that allows it to:

1. Receive events from source plugins (GitHub, Linear, etc.)
2. Process events through a rule-based system
3. Trigger actions in target plugins (Linear, Template Prompt, etc.)

## Integration with GitHub Plugin

### Event Reception

The Events plugin connects to the GitHub plugin's notification system:

```python
# In EventsPlugin.initialize()
github_plugin = get_plugin_instance("GitHub Integration")
if github_plugin and hasattr(github_plugin, 'github_manager'):
    github_manager = github_plugin.github_manager
    if hasattr(github_manager, 'notification_received'):
        github_manager.notification_received.connect(self._handle_github_notification)
```

### Event Processing

When a GitHub notification is received, it's processed and converted to an event:

```python
# In EventsPlugin._handle_github_notification()
if notification.type == "pull_request" and notification.action == "opened":
    event_type = "github_pr_created"
elif notification.type == "pull_request" and notification.action in ["synchronize", "edited"]:
    event_type = "github_pr_updated"
# ...
```

### Action Execution

The Events plugin can trigger GitHub actions like auto-merging PRs:

```python
# In EventManager._handle_auto_merge_pr()
success = pr_handler.auto_merge_pr(repo, pr_number)
```

## Integration with Linear Plugin

### Event Reception

The Events plugin connects to the Linear plugin's notification system:

```python
# In EventsPlugin.initialize()
linear_plugin = get_plugin_instance("Linear Integration")
if linear_plugin and hasattr(linear_plugin, 'integration'):
    linear_integration = linear_plugin.integration
    if hasattr(linear_integration, 'issue_created'):
        linear_integration.issue_created.connect(self._handle_linear_issue_created)
```

### Event Processing

When a Linear notification is received, it's processed and converted to an event:

```python
# In EventsPlugin._handle_linear_issue_created()
event_type_enum = EventType.LINEAR_ISSUE_CREATED
self.event_manager.trigger_event(event_type_enum, issue_data)
```

### Action Execution

The Events plugin can trigger Linear actions like creating issues:

```python
# In EventManager._handle_create_linear_issue()
issue = linear_client.create_issue(title, description, team_id)
```

## Integration with Template Prompt Plugin

### Template Usage

The Events plugin uses the Template Prompt plugin to render templates:

```python
# In EventManager._render_template()
from Toolbar.plugins.templateprompt.template_engine import TemplateEngine
template_engine = TemplateEngine()
rendered_text = template_engine.render(template, data)
```

### Action Execution

The Events plugin can trigger Template Prompt actions like sending prompts:

```python
# In EventManager._handle_send_prompt()
prompt = self._render_template(prompt_template, data)
# Send the prompt to the target
```

## Integration with Auto Scripting Plugin

### Script Execution

The Events plugin uses the Auto Scripting plugin to run custom scripts:

```python
# In EventManager._handle_run_script()
from Toolbar.plugins.autoscripting.script_runner import ScriptRunner
script_runner = ScriptRunner()
result = script_runner.run_script(script_id, script_params)
```

## Adding New Plugin Integrations

To add a new plugin integration to the Events plugin:

1. Add event reception code in `EventsPlugin.initialize()`
2. Add event handling methods in `EventsPlugin`
3. Add action handling methods in `EventManager`
4. Update the event and action types in `event_system.py`
5. Update the UI to support the new event and action types

Example for adding a new plugin integration:

```python
# In EventsPlugin.initialize()
new_plugin = get_plugin_instance("New Plugin")
if new_plugin and hasattr(new_plugin, 'notification_system'):
    new_plugin.notification_system.notification_received.connect(self._handle_new_plugin_notification)

# Add event handling method
def _handle_new_plugin_notification(self, notification):
    # Process notification and trigger event
    event_type_enum = EventType.NEW_PLUGIN_EVENT
    self.event_manager.trigger_event(event_type_enum, notification.data)

# In EventManager
def _handle_new_plugin_action(self, action, data):
    # Execute action in the new plugin
    # ...
```

## Plugin Communication Flow

The overall communication flow between plugins is:

1. Source Plugin (GitHub/Linear) → Events Plugin
   - Events are sent via Qt signals and slots
   - Event data is passed as JSON-serializable dictionaries

2. Events Plugin (Internal) → Event Manager
   - Events are processed through the rule-based system
   - Matching rules trigger actions

3. Event Manager → Target Plugin (Linear/Template Prompt)
   - Actions are executed via plugin APIs
   - Results are logged and can trigger further events

## Troubleshooting Interconnection Issues

If you encounter issues with plugin interconnection:

1. Check that all required plugins are installed and enabled
2. Verify that the plugin versions are compatible
3. Check the Toolbar logs for error messages
4. Ensure that the plugin APIs haven't changed
5. Test each integration point separately

## Advanced Interconnection Features

### Event Chaining

Events can be chained to create complex workflows:

```
GitHub PR Created → Create Linear Issue → Send Prompt
```

### Conditional Execution

Actions can be conditionally executed based on event data:

```
GitHub PR Created → [If PR contains .md files] → Auto-merge PR
```

### Data Transformation

Event data can be transformed before being passed to actions:

```
GitHub PR Created → [Extract PR title and URL] → Create Linear Issue with title and URL
```

## Future Interconnection Improvements

Planned improvements for plugin interconnection:

1. Dynamic plugin discovery and integration
2. Standardized event and action interfaces
3. Plugin-specific configuration UI
4. Event history and analytics
5. Advanced workflow visualization
