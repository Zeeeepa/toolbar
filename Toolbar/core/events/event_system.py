#!/usr/bin/env python3
import os
import sys
import json
import logging
import uuid
from enum import Enum
from typing import Dict, List, Any, Optional, Type, Callable, Set, Union, Tuple

from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Types of events that can be triggered."""
    GITHUB_PR_CREATED = "GitHub PR Created"
    GITHUB_PR_UPDATED = "GitHub PR Updated"
    GITHUB_PR_MERGED = "GitHub PR Merged"
    GITHUB_BRANCH_CREATED = "GitHub Branch Created"
    LINEAR_ISSUE_CREATED = "Linear Issue Created"
    LINEAR_ISSUE_UPDATED = "Linear Issue Updated"
    CUSTOM = "Custom Event"

class ActionType(Enum):
    """Types of actions that can be executed."""
    SEND_PROMPT = "Send Prompt"
    CREATE_LINEAR_ISSUE = "Create Linear Issue"
    AUTO_MERGE_PR = "Auto-Merge PR"
    RUN_SCRIPT = "Run Script"
    CUSTOM = "Custom Action"

class Condition:
    """Condition for event triggers."""
    
    def __init__(self, field: str, operator: str, value: Any):
        """Initialize the condition."""
        self.field = field
        self.operator = operator
        self.value = value
    
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Evaluate the condition against the given data."""
        if self.field not in data:
            return False
        
        field_value = data[self.field]
        
        if self.operator == "equals":
            return field_value == self.value
        elif self.operator == "not_equals":
            return field_value != self.value
        elif self.operator == "contains":
            return self.value in field_value
        elif self.operator == "not_contains":
            return self.value not in field_value
        elif self.operator == "starts_with":
            return str(field_value).startswith(str(self.value))
        elif self.operator == "ends_with":
            return str(field_value).endswith(str(self.value))
        elif self.operator == "greater_than":
            return field_value > self.value
        elif self.operator == "less_than":
            return field_value < self.value
        elif self.operator == "regex_match":
            import re
            return bool(re.match(self.value, str(field_value)))
        else:
            return False

class ActionParameter:
    """Parameter for an action."""
    
    def __init__(self, name: str, value: Any):
        """Initialize the action parameter."""
        self.name = name
        self.value = value

class Action:
    """Action to be executed when an event is triggered."""
    
    def __init__(self, id: str, name: str, action_type: ActionType, parameters: List[ActionParameter], enabled: bool = True):
        """Initialize the action."""
        self.id = id
        self.name = name
        self.action_type = action_type
        self.parameters = parameters
        self.enabled = enabled
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the action with the given data."""
        if not self.enabled:
            return {"success": False, "message": "Action is disabled"}
        
        try:
            # Get parameters as a dictionary
            params = {param.name: param.value for param in self.parameters}
            
            # Execute based on action type
            if self.action_type == ActionType.SEND_PROMPT:
                return self._execute_send_prompt(params, data)
            elif self.action_type == ActionType.CREATE_LINEAR_ISSUE:
                return self._execute_create_linear_issue(params, data)
            elif self.action_type == ActionType.AUTO_MERGE_PR:
                return self._execute_auto_merge_pr(params, data)
            elif self.action_type == ActionType.RUN_SCRIPT:
                return self._execute_run_script(params, data)
            else:
                return {"success": False, "message": f"Unsupported action type: {self.action_type.value}"}
        
        except Exception as e:
            logger.error(f"Error executing action {self.name}: {e}", exc_info=True)
            return {"success": False, "message": str(e)}
    
    def _execute_send_prompt(self, params: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the send prompt action."""
        # Get parameters
        prompt_template = params.get("prompt_template", "")
        target = params.get("target", "clipboard")
        
        # Replace variables in the prompt template
        prompt = self._replace_variables(prompt_template, data)
        
        # Send the prompt to the target
        if target == "clipboard":
            # Copy to clipboard
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(prompt)
            return {"success": True, "message": "Prompt copied to clipboard"}
        else:
            # TODO: Implement other targets (e.g., specific applications)
            return {"success": False, "message": f"Unsupported target: {target}"}
    
    def _execute_create_linear_issue(self, params: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the create Linear issue action."""
        # Get parameters
        team_id = params.get("team_id", "")
        title_template = params.get("title_template", "")
        description_template = params.get("description_template", "")
        
        # Replace variables in the templates
        title = self._replace_variables(title_template, data)
        description = self._replace_variables(description_template, data)
        
        # TODO: Implement Linear API integration
        return {"success": False, "message": "Linear API integration not implemented yet"}
    
    def _execute_auto_merge_pr(self, params: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the auto-merge PR action."""
        # Get parameters
        repo = params.get("repo", "")
        pr_number = params.get("pr_number", "")
        
        # TODO: Implement GitHub API integration
        return {"success": False, "message": "GitHub API integration not implemented yet"}
    
    def _execute_run_script(self, params: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the run script action."""
        # Get parameters
        script_id = params.get("script_id", "")
        
        # TODO: Implement script execution
        return {"success": False, "message": "Script execution not implemented yet"}
    
    def _replace_variables(self, template: str, data: Dict[str, Any]) -> str:
        """Replace variables in a template with values from data."""
        result = template
        
        for key, value in data.items():
            result = result.replace(f"{{{key}}}", str(value))
        
        return result

class EventTrigger:
    """Trigger for an event."""
    
    def __init__(self, id: str, name: str, event_type: EventType, conditions: List[Condition], enabled: bool = True):
        """Initialize the event trigger."""
        self.id = id
        self.name = name
        self.event_type = event_type
        self.conditions = conditions
        self.enabled = enabled
    
    def matches(self, event_type: EventType, data: Dict[str, Any]) -> bool:
        """Check if the trigger matches the given event type and data."""
        if not self.enabled:
            return False
        
        if self.event_type != event_type:
            return False
        
        # Check all conditions
        for condition in self.conditions:
            if not condition.evaluate(data):
                return False
        
        return True

class Event:
    """Event that can be triggered and execute actions."""
    
    def __init__(self, id: str, name: str, description: str, trigger: EventTrigger, actions: List[Action], enabled: bool = True):
        """Initialize the event."""
        self.id = id
        self.name = name
        self.description = description
        self.trigger = trigger
        self.actions = actions
        self.enabled = enabled
    
    def matches(self, event_type: EventType, data: Dict[str, Any]) -> bool:
        """Check if the event matches the given event type and data."""
        if not self.enabled:
            return False
        
        return self.trigger.matches(event_type, data)
    
    def execute(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute all actions for the event."""
        results = []
        
        for action in self.actions:
            if action.enabled:
                result = action.execute(data)
                results.append(result)
        
        return results

class EventManager(QObject):
    """Manager for events and triggers."""
    
    # Signals
    event_triggered = pyqtSignal(EventType, dict)
    action_executed = pyqtSignal(Action, dict)
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the event manager."""
        super().__init__()
        self.events = {}
        self.config = config or {}
        
        # Load events from config
        self._load_events()
    
    def _load_events(self):
        """Load events from the configuration."""
        events_data = self.config.get("events", [])
        
        for event_data in events_data:
            try:
                # Create trigger
                trigger_data = event_data.get("trigger", {})
                trigger = EventTrigger(
                    id=trigger_data.get("id", str(uuid.uuid4())),
                    name=trigger_data.get("name", ""),
                    event_type=EventType(trigger_data.get("event_type", EventType.CUSTOM.value)),
                    conditions=[
                        Condition(
                            field=c.get("field", ""),
                            operator=c.get("operator", "equals"),
                            value=c.get("value", "")
                        )
                        for c in trigger_data.get("conditions", [])
                    ],
                    enabled=trigger_data.get("enabled", True)
                )
                
                # Create actions
                actions = []
                for action_data in event_data.get("actions", []):
                    action = Action(
                        id=action_data.get("id", str(uuid.uuid4())),
                        name=action_data.get("name", ""),
                        action_type=ActionType(action_data.get("action_type", ActionType.CUSTOM.value)),
                        parameters=[
                            ActionParameter(
                                name=p.get("name", ""),
                                value=p.get("value", "")
                            )
                            for p in action_data.get("parameters", [])
                        ],
                        enabled=action_data.get("enabled", True)
                    )
                    actions.append(action)
                
                # Create event
                event = Event(
                    id=event_data.get("id", str(uuid.uuid4())),
                    name=event_data.get("name", ""),
                    description=event_data.get("description", ""),
                    trigger=trigger,
                    actions=actions,
                    enabled=event_data.get("enabled", True)
                )
                
                # Add to events
                self.events[event.id] = event
            
            except Exception as e:
                logger.error(f"Error loading event: {e}", exc_info=True)
    
    def _save_events(self):
        """Save events to the configuration."""
        events_data = []
        
        for event in self.events.values():
            try:
                # Create trigger data
                trigger_data = {
                    "id": event.trigger.id,
                    "name": event.trigger.name,
                    "event_type": event.trigger.event_type.value,
                    "conditions": [
                        {
                            "field": condition.field,
                            "operator": condition.operator,
                            "value": condition.value
                        }
                        for condition in event.trigger.conditions
                    ],
                    "enabled": event.trigger.enabled
                }
                
                # Create actions data
                actions_data = []
                for action in event.actions:
                    action_data = {
                        "id": action.id,
                        "name": action.name,
                        "action_type": action.action_type.value,
                        "parameters": [
                            {
                                "name": parameter.name,
                                "value": parameter.value
                            }
                            for parameter in action.parameters
                        ],
                        "enabled": action.enabled
                    }
                    actions_data.append(action_data)
                
                # Create event data
                event_data = {
                    "id": event.id,
                    "name": event.name,
                    "description": event.description,
                    "trigger": trigger_data,
                    "actions": actions_data,
                    "enabled": event.enabled
                }
                
                events_data.append(event_data)
            
            except Exception as e:
                logger.error(f"Error saving event: {e}", exc_info=True)
        
        # Update config
        self.config["events"] = events_data
    
    def trigger_event(self, event_type: EventType, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Trigger an event with the given type and data."""
        results = []
        
        # Find matching events
        for event in self.events.values():
            if event.matches(event_type, data):
                # Execute the event
                event_results = event.execute(data)
                results.extend(event_results)
                
                # Emit signals
                self.event_triggered.emit(event_type, data)
                
                for action, result in zip(event.actions, event_results):
                    self.action_executed.emit(action, result)
        
        return results
    
    def add_event(self, event: Event) -> None:
        """Add an event to the manager."""
        self.events[event.id] = event
        self._save_events()
    
    def update_event(self, event_id: str, event: Event) -> None:
        """Update an event in the manager."""
        self.events[event_id] = event
        self._save_events()
    
    def delete_event(self, event_id: str) -> None:
        """Delete an event from the manager."""
        if event_id in self.events:
            del self.events[event_id]
            self._save_events()
    
    def get_event(self, event_id: str) -> Optional[Event]:
        """Get an event by ID."""
        return self.events.get(event_id)
    
    def get_all_events(self) -> List[Event]:
        """Get all events."""
        return list(self.events.values())
