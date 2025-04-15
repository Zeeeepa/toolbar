# Toolbar

A modular toolbar application with plugin support for various integrations.

## Features

- Plugin-based architecture for easy extensibility
- GitHub integration (via plugin)
- Linear integration (via plugin)
- Script management (via plugin)
- Prompt templates (via plugin)
- Customizable UI - Settings of toolbar


Create a `.env` file in the project root with the following variables:

```env
# GitHub Configuration
GITHUB_USERNAME=your_github_username
GITHUB_TOKEN=your_github_token
NGROK_AUTH_TOKEN=your_ngrok_token

# Linear Configuration
LINEAR_API_KEY=your_linear_api_key
```

### Plugin Configuration

Each plugin can be configured through the toolbar's settings dialog. Plugins are loaded from the `Toolbar/plugins` directory.

# Extensible Toolbar

A toolbar utility for quick access to plugin modules like  GitHub linear, scriptautomation, prompttemplates.

## Features

- Transparent topbar that stays on top of other windows
- Allows adding programs as launchable shortcuts. (.py, .bat mostly)
- Drag-and-drop reordering of scripts

- Action/command recorder for automating repetitive tasks
- Export recorded actions as Python scripts or batch files

   ```

## GitHub Plugin

- GitHub integration for PR and branch notifications
- GitHub Projects integration with notification badges
The toolbar provides real-time notifications for:
- New pull requests
- New branches
- Pull request review requests

1. Click the "GitHub" button in the toolbar
2. Enter your GitHub username and personal access token
3. Click "Validate" to test your credentials
4. Click "Save" to store your credentials

### Notification Features

- **Notification Badge**: Shows the number of unread notifications
- **Notification Panel**: Click the badge to show/hide the notification panel
- **Notification Cards**: Each notification appears as a card with:
  - Icon indicating the type (PR, new branch)
  - Title of the PR or branch
  - Repository name and timestamp
  - "NEW" badge for recent notifications
  
### Interacting with Notifications

- **Left-click** on a notification to open it in your browser
- **Hover** over a notification to see more details
- **Right-click** on a notification for options:
  - Open in Browser: Open the PR or branch in your browser
  - Dismiss: Remove the notification

### GitHub Projects

The toolbar now includes a GitHub Projects feature that allows you to:

- Pin your favorite GitHub repositories to the toolbar
- See notifications for specific projects
- Quickly access project pages and notifications

#### Setting Up GitHub Projects

1. Click the "Manage Projects" button in the projects toolbar
2. Check the repositories you want to pin to the toolbar
3. Click "Close" to save your changes

#### Project Features

- **Project Icons**: Each pinned project appears as an icon in the toolbar
- **Notification Badges**: Shows the number of unread notifications for each project
- **Quick Access**: Click on a project icon to open its GitHub page
- **Contextual Notifications**: When a project has notifications, clicking the icon opens the first notification

#### Interacting with Projects

- **Left-click** on a project icon to:
  - Open the first notification if there are any
  - Open the project page if there are no notifications
- **Right-click** on a project icon for options:
  - Open Project: Open the project page in your browser
  - Notifications: View and open specific notifications
  - Clear Notifications: Clear all notifications for this project
  - Unpin Project: Remove the project from the toolbar


### Notification Behavior

Notifications will:
- Be cleared when you click on them to open in browser

## Action Recorder

The Action Recorder allows you to record mouse movements, clicks, keyboard inputs, and commands, then save them as scripts that can be added to the toolbar.

### How to Use the Action Recorder

1. Click the "Record Actions" button in the toolbar
2. Click "Start Recording" to begin capturing your actions
3. Perform the actions you want to record (mouse movements, clicks, keyboard inputs)
4. Press Esc or click "Stop Recording" to finish recording
5. Edit your recorded actions:
   - Double-click an action to edit its properties
   - Use the "Add Delay" button to add pauses between actions
   - Use the "Add Command" button to insert shell commands
   - Use the context menu (right-click) for more options
6. Click "Export as Script" to save your actions as a Python script or batch file
7. Choose whether to add the script to the toolbar

### Action Types

- **Mouse Movements**: Records cursor position changes
- **Mouse Clicks**: Records button clicks and their screen positions
- **Keyboard Inputs**: Records key presses and releases
- **Delays**: Adds pauses between actions
- **Commands**: Executes shell commands

## Adding Scripts to the Toolbar

1. Click the "Add Script" button in the toolbar
2. Select a Python script (.py) or batch file (.bat)
3. Enter a name for the script
4. Choose an icon (optional)

## Customizing the Toolbar

- **Reordering Scripts**: Drag and drop script buttons to change their order
- **Editing Scripts**: Right-click a script button and select "Edit Script"
- **Changing Icons**: Right-click a script button and select "Edit Icon"
- **Removing Scripts**: Right-click a script button and select "Delete Script"

## License

This project is open source and available under the MIT License.

