# GitHub Plugin for Toolkit

This plugin provides GitHub integration for the Toolkit application, allowing you to monitor your GitHub repositories, receive notifications for new pull requests and branches, and pin your favorite repositories to the toolbar.

## Features

- GitHub repository monitoring with real-time notifications
- Project pinning functionality to keep your favorite repos accessible
- Notification system for PRs and new branches
- Settings panel for configuring GitHub credentials
- Project management dialog for selecting which repos to display
- Notification badges on project icons and the GitHub icon
- Configurable notification preferences (PR and branch notifications)

## Installation

1. Make sure you have the required dependencies installed:
   ```
   pip install PyGithub requests
   ```

2. The plugin will be automatically loaded when Toolkit starts.

## Usage

1. The GitHub icon appears in the middle of the toolbar.
2. Click on the GitHub icon to access the plugin menu.
3. Select "Settings" to configure your GitHub API token.
4. Select "Projects" to choose which repositories to pin to the toolbar.
5. Notifications will appear when there are new PRs or branches in your pinned repositories.
6. Click on a notification to open it in your browser.
7. Click on a project icon to open the repository in your browser.

## Configuration

The plugin stores its configuration in the Toolkit configuration file. The following settings are available:

- `github.token`: Your GitHub API token
- `github.notify_prs`: Whether to notify for new pull requests (true/false)
- `github.notify_branches`: Whether to notify for new branches (true/false)
- `github.monitor_interval`: How often to check for updates (in seconds)

## Creating a GitHub API Token

1. Go to [GitHub Token Settings](https://github.com/settings/tokens)
2. Click "Generate new token"
3. Give your token a name (e.g., "Toolkit GitHub Plugin")
4. Select the "repo" scope
5. Click "Generate token"
6. Copy the token and paste it into the plugin settings

## License

This plugin is released under the same license as the Toolkit application.
