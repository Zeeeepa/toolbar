cat > Toolbar/core/events/event_system.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
import json
import logging
import threading
import time
from typing import Dict, List, Any, Optional, Type, Callable, Set, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field, asdict
from PyQt5.QtCore import QObject, pyqtSignal
logger = logging.getLogger(__name__)
class EventType(Enum):
    """Enum representing the types of events."""
    GITHUB_PR_CREATED = "github_pr_created"
    GITHUB_PR_UPDATED = "github_pr_updated"
    GITHUB_PR_MERGED = "github_pr_merged"
    GITHUB_BRANCH_CREATED = "github_branch_created"
    GITHUB_REPO_UPDATED = "github_repo_updated"
    LINEAR_ISSUE_CREATED = "linear_issue_created"
    LINEAR_ISSUE_UPDATED = "linear_issue_updated"
    LINEAR_ISSUE_CLOSED = "linear_issue_closed"
    CUSTOM = "custom"
class ActionType(Enum):
    """Enum representing the types of actions."""
    SEND_PROMPT = "send_prompt"
    CREATE_LINEAR_ISSUE = "create_linear_issue"
    AUTO_MERGE_PR = "auto_merge_pr"
    RUN_SCRIPT = "run_script"
    CUSTOM = "custom"
@dataclass
class Condition:
    """Class representing a condition for an event trigger."""
    field: str
    operator: str  # "equals", "contains", "startswith", "endswith", "regex"
    value: Any
    
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Evaluate the condition against the data."""
        # Get the field value using dot notation
        field_parts = self.field.split('.')
        current = data
        for part in field_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        
        # Evaluate based on operator
        if self.operator == "equals":
            return current == self.value
        elif self.operator == "contains":
            return self.value in current if isinstance(current, (str, list, dict)) else False
        elif self.operator == "startswith":
            return current.startswith(self.value) if isinstance(current, str) else False
        elif self.operator == "endswith":
            return current.endswith(self.value) if isinstance(current, str) else False
        elif self.operator == "regex":
            import re
            return bool(re.match(self.value, current)) if isinstance(current, str) else False
        
        return False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Condition':
        """Create a Condition from a dictionary."""
        return cls(
            field=data.get("field", ""),
            operator=data.get("operator", "equals"),
            value=data.get("value")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
@dataclass
class EventTrigger:
    """Class representing an event trigger."""
    id: str
    name: str
    event_type: EventType
    conditions: List[Condition] = field(default_factory=list)
    enabled: bool = True
    
    def matches(self, event_type: EventType, data: Dict[str, Any]) -> bool:
        """Check if the event matches this trigger."""
        # Check event type
        if self.event_type != event_type and self.event_type != EventType.CUSTOM:
            return False
        
        # If no conditions, match all events of this type
        if not self.conditions:
            return True
        
        # Check all conditions
        for condition in self.conditions:
            if not condition.evaluate(data):
                return False
        
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventTrigger':
        """Create an EventTrigger from a dictionary."""
        # Convert event_type string to enum
        event_type_str = data.get("event_type", "custom")
        try:
            event_type = EventType(event_type_str)
        except ValueError:
            event_type = EventType.CUSTOM
        
        # Convert conditions list
        conditions = []
        for cond in data.get("conditions", []):
            conditions.append(Condition.from_dict(cond))
        
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            event_type=event_type,
            conditions=conditions,
            enabled=data.get("enabled", True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert enums to strings
        data["event_type"] = self.event_type.value
        # Convert conditions to dicts
        data["conditions"] = [cond.to_dict() for cond in self.conditions]
        return data
@dataclass
class ActionParameter:
    """Class representing a parameter for an action."""
    name: str
    value: Any
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionParameter':
        """Create an ActionParameter from a dictionary."""
        return cls(
            name=data.get("name", ""),
            value=data.get("value")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
@dataclass
class Action:
    """Class representing an action to be executed."""
    id: str
    name: str
    action_type: ActionType
    parameters: List[ActionParameter] = field(default_factory=list)
    enabled: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """Create an Action from a dictionary."""
        # Convert action_type string to enum
        action_type_str = data.get("action_type", "custom")
        try:
            action_type = ActionType(action_type_str)
        except ValueError:
            action_type = ActionType.CUSTOM
        
        # Convert parameters list
        parameters = []
        for param in data.get("parameters", []):
            parameters.append(ActionParameter.from_dict(param))
        
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            action_type=action_type,
            parameters=parameters,
            enabled=data.get("enabled", True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert enums to strings
        data["action_type"] = self.action_type.value
        # Convert parameters to dicts
        data["parameters"] = [param.to_dict() for param in self.parameters]
        return data
@dataclass
class Event:
    """Class representing an event configuration."""
    id: str
    name: str
    description: str
    trigger: EventTrigger
    actions: List[Action] = field(default_factory=list)
    enabled: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create an Event from a dictionary."""
        # Convert trigger
        trigger_data = data.get("trigger", {})
        trigger = EventTrigger.from_dict(trigger_data)
        
        # Convert actions list
        actions = []
        for action_data in data.get("actions", []):
            actions.append(Action.from_dict(action_data))
        
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            trigger=trigger,
            actions=actions,
            enabled=data.get("enabled", True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert trigger to dict
        data["trigger"] = self.trigger.to_dict()
        # Convert actions to dicts
        data["actions"] = [action.to_dict() for action in self.actions]
        return data
class EventManager(QObject):
    """Manager for handling events and actions."""
    
    event_triggered = pyqtSignal(object, object)  # event_type, data
    action_executed = pyqtSignal(object, object)  # action, result
    
    def __init__(self, config):
        """Initialize the event manager."""
        super().__init__()
        self.config = config
        self.events = []
        self.action_handlers = {}
        
        # Load events from configuration
        self.load_events()
        
        # Register default action handlers
        self.register_default_action_handlers()
    
    def load_events(self):
        """Load events from configuration."""
        try:
            events_data = self.config.get_setting("events", [])
            self.events = []
            
            for event_data in events_data:
                try:
                    event = Event.from_dict(event_data)
                    self.events.append(event)
                except Exception as e:
                    logger.error(f"Error loading event: {e}", exc_info=True)
            
            logger.info(f"Loaded {len(self.events)} events")
        except Exception as e:
            logger.error(f"Error loading events: {e}", exc_info=True)
    
    def save_events(self):
        """Save events to configuration."""
        try:
            events_data = [event.to_dict() for event in self.events]
            self.config.set_setting("events", events_data)
            self.config.save()
            logger.info(f"Saved {len(self.events)} events")
        except Exception as e:
            logger.error(f"Error saving events: {e}", exc_info=True)
    
    def register_action_handler(self, action_type: ActionType, handler: Callable[[Action, Dict[str, Any]], Any]):
        """Register a handler for an action type."""
        self.action_handlers[action_type] = handler
        logger.info(f"Registered handler for action type: {action_type.value}")
    
    def register_default_action_handlers(self):
        """Register default action handlers."""
        # Register handlers for built-in action types
        self.register_action_handler(ActionType.SEND_PROMPT, self._handle_send_prompt)
        self.register_action_handler(ActionType.CREATE_LINEAR_ISSUE, self._handle_create_linear_issue)
        self.register_action_handler(ActionType.AUTO_MERGE_PR, self._handle_auto_merge_pr)
        self.register_action_handler(ActionType.RUN_SCRIPT, self._handle_run_script)
    
    def trigger_event(self, event_type: EventType, data: Dict[str, Any]):
        """Trigger an event and execute matching actions."""
        logger.info(f"Event triggered: {event_type.value}")
        
        # Emit event triggered signal
        self.event_triggered.emit(event_type, data)
        
        # Find matching events
        matching_events = []
        for event in self.events:
            if event.enabled and event.trigger.matches(event_type, data):
                matching_events.append(event)
        
        logger.info(f"Found {len(matching_events)} matching events")
        
        # Execute actions for matching events
        for event in matching_events:
            for action in event.actions:
                if action.enabled:
                    self._execute_action(action, data)
    
    def _execute_action(self, action: Action, data: Dict[str, Any]):
        """Execute an action."""
        logger.info(f"Executing action: {action.name} ({action.action_type.value})")
        
        try:
            # Get the handler for this action type
            handler = self.action_handlers.get(action.action_type)
            
            if handler:
                # Execute the handler
                result = handler(action, data)
                
                # Emit action executed signal
                self.action_executed.emit(action, result)
                
                logger.info(f"Action executed successfully: {action.name}")
                return result
            else:
                logger.warning(f"No handler registered for action type: {action.action_type.value}")
        except Exception as e:
            logger.error(f"Error executing action {action.name}: {e}", exc_info=True)
        
        return None
    
    def _handle_send_prompt(self, action: Action, data: Dict[str, Any]):
        """Handle send prompt action."""
        # Get parameters
        prompt_template = None
        target = None
        
        for param in action.parameters:
            if param.name == "prompt_template":
                prompt_template = param.value
            elif param.name == "target":
                target = param.value
        
        if not prompt_template:
            logger.error("Missing prompt_template parameter")
            return None
        
        if not target:
            logger.error("Missing target parameter")
            return None
        
        # Render the prompt template with data
        prompt = self._render_template(prompt_template, data)
        
        # Send the prompt to the target
        if target == "clipboard":
            # Copy to clipboard
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QMimeData
            clipboard = QApplication.clipboard()
            mime_data = QMimeData()
            mime_data.setText(prompt)
            clipboard.setMimeData(mime_data)
            return {"status": "success", "message": "Prompt copied to clipboard"}
        elif target.startswith("coordinates:"):
            # Send to coordinates
            coords = target.split(":", 1)[1].strip()
            x, y = map(int, coords.split(","))
            
            # Use pyautogui to click and type
            try:
                import pyautogui
                pyautogui.click(x, y)
                pyautogui.typewrite(prompt)
                pyautogui.press("enter")
                return {"status": "success", "message": f"Prompt sent to coordinates ({x}, {y})"}
            except Exception as e:
                logger.error(f"Error sending prompt to coordinates: {e}", exc_info=True)
                return {"status": "error", "message": str(e)}
        
        return {"status": "error", "message": f"Unknown target: {target}"}
    
    def _handle_create_linear_issue(self, action: Action, data: Dict[str, Any]):
        """Handle create Linear issue action."""
        # Get parameters
        team_id = None
        title_template = None
        description_template = None
        
        for param in action.parameters:
            if param.name == "team_id":
                team_id = param.value
            elif param.name == "title_template":
                title_template = param.value
            elif param.name == "description_template":
                description_template = param.value
        
        if not title_template:
            logger.error("Missing title_template parameter")
            return None
        
        # Render the templates with data
        title = self._render_template(title_template, data)
        description = self._render_template(description_template, data) if description_template else ""
        
        # Create the Linear issue
        # This would typically use a Linear API client
        # For now, just log the action
        logger.info(f"Would create Linear issue: {title}")
        logger.info(f"Team ID: {team_id}")
        logger.info(f"Description: {description}")
        
        return {
            "status": "success",
            "message": "Linear issue creation simulated",
            "title": title,
            "description": description,
            "team_id": team_id
        }
    
    def _handle_auto_merge_pr(self, action: Action, data: Dict[str, Any]):
        """Handle auto-merge PR action."""
        # Get parameters
        repo = None
        pr_number = None
        
        for param in action.parameters:
            if param.name == "repo":
                repo = param.value
            elif param.name == "pr_number":
                pr_number = param.value
        
        # If PR number not provided, try to get it from the event data
        if not pr_number and "pull_request" in data and "number" in data["pull_request"]:
            pr_number = data["pull_request"]["number"]
        
        # If repo not provided, try to get it from the event data
        if not repo and "repository" in data and "full_name" in data["repository"]:
            repo = data["repository"]["full_name"]
        
        if not repo or not pr_number:
            logger.error("Missing repo or PR number")
            return None
        
        # Auto-merge the PR
        # This would typically use a GitHub API client
        # For now, just log the action
        logger.info(f"Would auto-merge PR #{pr_number} in {repo}")
        
        return {
            "status": "success",
            "message": "PR auto-merge simulated",
            "repo": repo,
            "pr_number": pr_number
        }
    
    def _handle_run_script(self, action: Action, data: Dict[str, Any]):
        """Handle run script action."""
        # Get parameters
        script_id = None
        script_params = {}
        
        for param in action.parameters:
            if param.name == "script_id":
                script_id = param.value
            elif param.name.startswith("param_"):
                param_name = param.name[6:]  # Remove "param_" prefix
                script_params[param_name] = param.value
        
        if not script_id:
            logger.error("Missing script_id parameter")
            return None
        
        # Run the script
        # This would typically use a script runner
        # For now, just log the action
        logger.info(f"Would run script: {script_id}")
        logger.info(f"Script parameters: {script_params}")
        
        return {
            "status": "success",
            "message": "Script execution simulated",
            "script_id": script_id,
            "parameters": script_params
        }
    
    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """Render a template with data."""
        # Simple template rendering with {variable} syntax
        result = template
        
        # Replace variables in the template
        import re
        for match in re.finditer(r'\{([^}]+)\}', template):
            var_name = match.group(1)
            var_parts = var_name.split('.')
            
            # Get the variable value
            var_value = data
            try:
                for part in var_parts:
                    if isinstance(var_value, dict) and part in var_value:
                        var_value = var_value[part]
                    else:
                        var_value = ""
                        break
                
                # Convert to string
                if not isinstance(var_value, str):
                    var_value = str(var_value)
                
                # Replace in the template
                result = result.replace(match.group(0), var_value)
            except Exception as e:
                logger.error(f"Error rendering template variable {var_name}: {e}", exc_info=True)
        
        return result
    
    def add_event(self, event: Event):
        """Add a new event."""
        self.events.append(event)
        self.save_events()
        logger.info(f"Added event: {event.name}")
    
    def update_event(self, event_id: str, event: Event):
        """Update an existing event."""
        for i, existing_event in enumerate(self.events):
            if existing_event.id == event_id:
                self.events[i] = event
                self.save_events()
                logger.info(f"Updated event: {event.name}")
                return True
        
        logger.warning(f"Event not found: {event_id}")
        return False
    
    def delete_event(self, event_id: str):
        """Delete an event."""
        for i, event in enumerate(self.events):
            if event.id == event_id:
                del self.events[i]
                self.save_events()
                logger.info(f"Deleted event: {event_id}")
                return True
        
        logger.warning(f"Event not found: {event_id}")
        return False
    
    def get_event(self, event_id: str) -> Optional[Event]:
        """Get an event by ID."""
        for event in self.events:
            if event.id == event_id:
                return event
        
        logger.warning(f"Event not found: {event_id}")
        return None
    
    def get_all_events(self) -> List[Event]:
        """Get all events."""
        return self.events
EOF