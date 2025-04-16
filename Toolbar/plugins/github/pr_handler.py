"""
GitHub PR handler module.
"""

def setup_pr_handler(event_bus):
    """Set up GitHub PR event handlers."""
    event_bus.register_handler("github_pr_created", handle_pr_created)
    event_bus.register_handler("github_pr_updated", handle_pr_updated)
    event_bus.register_handler("github_pr_closed", handle_pr_closed)

def handle_pr_created(event):
    """Handle PR created event."""
    pr = event.get("pull_request")
    if pr:
        print(f"PR #{pr.number} created: {pr.title}")

def handle_pr_updated(event):
    """Handle PR updated event."""
    pr = event.get("pull_request")
    if pr:
        print(f"PR #{pr.number} updated: {pr.title}")

def handle_pr_closed(event):
    """Handle PR closed event."""
    pr = event.get("pull_request")
    if pr:
        print(f"PR #{pr.number} closed: {pr.title}")
