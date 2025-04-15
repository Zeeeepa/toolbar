# GitHub Plugin

The GitHub plugin integrates the Toolbar application with GitHub, providing features for monitoring repositories, handling webhooks, and managing notifications.

## Features

- **Repository Monitoring**: Automatically checks for new PRs and branches in your GitHub repositories.
- **Notifications**: Receive notifications for new PRs, branches, and other GitHub events.
- **Webhook Support**: Set up webhooks to receive real-time notifications for GitHub events.
- **Project Management**: Pin important repositories for quick access.

## Components

The GitHub plugin consists of the following components:

### Core Components

- **GitHubMonitor**: Monitors GitHub repositories for new PRs and branches.
- **GitHubManager**: Manages GitHub functionality and notifications.
- **WebhookHandler**: Handles incoming webhook requests from GitHub.
- **WebhookManager**: Manages webhook registrations with GitHub.
- **NgrokManager**: Manages ngrok tunnels for webhook support.

### UI Components

- **GitHubUI**: Main UI for the GitHub plugin.
- **GitHubSettingsDialog**: Dialog for configuring GitHub settings.
- **GitHubProjectsDialog**: Dialog for managing GitHub projects.
- **ProjectIconUI**: UI for displaying project icons.

## Configuration

The GitHub plugin can be configured through the GitHub settings dialog, which can be accessed from the toolbar. The following settings are available:

- **GitHub Credentials**: Set your GitHub username and API token.
- **Webhook Settings**: Configure webhook support for real-time notifications.
- **Monitoring Interval**: Set how often the plugin checks for updates.

## Usage

1. Click on the GitHub icon in the toolbar to open the GitHub UI.
2. Use the settings dialog to configure your GitHub credentials and other settings.
3. Pin important repositories for quick access.
4. Receive notifications for new PRs, branches, and other GitHub events.

## Dependencies

The GitHub plugin depends on the following Python packages:

- PyGithub: For interacting with the GitHub API.
- requests: For making HTTP requests.
- PyQt5: For the UI components.

## Plugin Structure

```
Toolbar/plugins/github/
├── __init__.py                # Plugin entry point
├── metadata.json              # Plugin metadata
├── github_manager.py          # GitHub manager
├── github/                    # GitHub module
│   ├── __init__.py            # Module entry point
│   ├── configure_github.py    # GitHub configuration
│   ├── models.py              # GitHub models
│   ├── monitor.py             # GitHub monitor
│   ├── ngrok_manager.py       # ngrok manager
│   ├── webhook_handler.py     # Webhook handler
│   └── webhook_manager.py     # Webhook manager
└── ui/                        # UI components
    ├── __init__.py            # UI module entry point
    ├── github_project_ui.py   # GitHub project UI
    ├── github_settings.py     # GitHub settings dialog
    ├── github_ui.py           # Main GitHub UI
    └── project_icon_ui.py     # Project icon UI
```
