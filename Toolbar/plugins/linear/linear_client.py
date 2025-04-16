"""
Linear client module.
"""

def setup_linear_client(event_bus):
    """Set up Linear event handlers."""
    event_bus.register_handler("linear_issue_created", handle_issue_created)
    event_bus.register_handler("linear_issue_updated", handle_issue_updated)
    event_bus.register_handler("linear_issue_closed", handle_issue_closed)

def handle_issue_created(event):
    """Handle issue created event."""
    issue = event.get("issue")
    if issue:
        print(f"Issue {issue.identifier} created: {issue.title}")

def handle_issue_updated(event):
    """Handle issue updated event."""
    issue = event.get("issue")
    if issue:
        print(f"Issue {issue.identifier} updated: {issue.title}")

def handle_issue_closed(event):
    """Handle issue closed event."""
    issue = event.get("issue")
    if issue:
        print(f"Issue {issue.identifier} closed: {issue.title}")
