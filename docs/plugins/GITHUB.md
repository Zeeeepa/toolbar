# GitHub Plugin

The GitHub plugin provides integration with GitHub repositories, allowing users to monitor repositories, receive notifications for pull requests and branches, and manage GitHub projects directly from the Toolbar application.

## Features

- **Repository Monitoring**: Automatically monitor GitHub repositories for changes
- **Notifications**: Receive notifications for new pull requests, branches, and other GitHub events
- **Webhook Integration**: Set up webhooks to receive real-time notifications from GitHub
- **Project Management**: Pin favorite repositories to the toolbar for quick access
- **Authentication**: Secure GitHub API authentication with personal access tokens

## Components

### Core Components

- **GitHubMonitor**: Monitors GitHub repositories for changes and manages webhook integration
- **GitHubManager**: Manages GitHub functionality and serves as a bridge between the monitor and UI
- **GitHubPlugin**: Main plugin class that initializes the GitHub integration

### Models

- **GitHubProject**: Represents a GitHub repository with its metadata and notifications
- **GitHubNotification**: Represents a notification from GitHub (PR, branch, etc.)

### UI Components

- **GitHubUI**: Main UI component for displaying GitHub notifications and projects
- **GitHubSettingsDialog**: Dialog for configuring GitHub settings
- **GitHubProjectsDialog**: Dialog for managing GitHub projects
- **ProjectWidget**: Widget for displaying a GitHub project with notification badge
- **NotificationWidget**: Widget for displaying a GitHub notification

### Webhook Components

- **WebhookManager**: Manages GitHub webhooks for repositories
- **WebhookHandler**: Handles GitHub webhook events
- **NgrokManager**: Manages ngrok tunneling for webhook integration

## Configuration

The GitHub plugin uses the following configuration settings:

- `github.username`: GitHub username
- `github.token`: GitHub API token
- `github.webhook_enabled`: Whether webhooks are enabled
- `github.webhook_port`: Port for the webhook server
- `github.ngrok_auth_token`: ngrok authentication token
- `github.pinned_projects`: List of pinned GitHub projects

## Usage

1. Configure GitHub credentials in the settings dialog
2. Pin repositories to the toolbar for quick access
3. Receive notifications for new pull requests and branches
4. Click on notifications to open them in the browser

## Dependencies

- PyGithub: Python library for the GitHub API
- ngrok: For webhook tunneling (optional)
