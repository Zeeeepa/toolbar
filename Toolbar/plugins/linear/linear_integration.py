import os
import json
import requests
import warnings
import logging
from PyQt5.QtCore import QObject, pyqtSignal

# Suppress PyQt5 deprecation warnings
warnings.filterwarnings("ignore", message=".*sipPyTypeDict.*")

# Set up logger
logger = logging.getLogger(__name__)

class LinearIssue:
    """
    Class representing a Linear issue.
    """
    def __init__(self, title="", description="", team_id=None, assignee_id=None, state_id=None, priority=None, labels=None):
        """
        Initialize a Linear issue.
        
        Args:
            title (str): Issue title
            description (str): Issue description
            team_id (str, optional): Team ID
            assignee_id (str, optional): Assignee ID
            state_id (str, optional): State ID
            priority (int, optional): Priority (0-4)
            labels (list, optional): List of label IDs
        """
        self.title = title
        self.description = description
        self.team_id = team_id
        self.assignee_id = assignee_id
        self.state_id = state_id
        self.priority = priority
        self.labels = labels or []
    
    def to_dict(self):
        """Convert issue to dictionary for API request."""
        data = {
            "title": self.title,
            "description": self.description,
        }
        
        if self.team_id:
            data["teamId"] = self.team_id
        
        if self.assignee_id:
            data["assigneeId"] = self.assignee_id
        
        if self.state_id:
            data["stateId"] = self.state_id
        
        if self.priority is not None:
            data["priority"] = self.priority
        
        if self.labels:
            data["labelIds"] = self.labels
        
        return data

class LinearIntegration(QObject):
    """
    Integration with Linear API.
    """
    issue_created = pyqtSignal(object)
    
    def __init__(self, config):
        """
        Initialize the Linear integration.
        
        Args:
            config (Config): Application configuration
        """
        super().__init__()
        self.config = config
        self.api_key = self.config.get_setting("linear_api_key", "")
        self.api_url = "https://api.linear.app/graphql"
        self.settings_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "linear_settings.json")
        
        # Default settings
        self.settings = {
            "default_team_id": "",
            "default_state_id": "",
            "default_template": "",
            "templates": []
        }
        
        # Load settings
        self.load_settings()
    
    def load_settings(self):
        """Load Linear settings from JSON file."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            except Exception as e:
                warnings.warn(f"Failed to load Linear settings: {str(e)}")
    
    def save_settings(self):
        """Save Linear settings to JSON file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            warnings.warn(f"Failed to save Linear settings: {str(e)}")
    
    def set_api_key(self, api_key):
        """
        Set the Linear API key.
        
        Args:
            api_key (str): Linear API key
        """
        self.api_key = api_key
        self.config.set_setting("linear_api_key", api_key)
    
    def create_issue(self, issue):
        """
        Create a new issue in Linear.
        
        Args:
            issue (LinearIssue): Issue to create
            
        Returns:
            dict: Response data if successful, None otherwise
        """
        if not self.api_key:
            warnings.warn("Linear API key not set")
            return None
        
        # Set default team ID if not provided
        if not issue.team_id and self.settings.get("default_team_id"):
            issue.team_id = self.settings.get("default_team_id")
        
        # Set default state ID if not provided
        if not issue.state_id and self.settings.get("default_state_id"):
            issue.state_id = self.settings.get("default_state_id")
        
        # Prepare GraphQL mutation
        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    title
                    url
                }
            }
        }
        """
        
        # Prepare variables
        variables = {
            "input": issue.to_dict()
        }
        
        # Send request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json={
                    "query": mutation,
                    "variables": variables
                }
            )
            
            # Check for errors
            if response.status_code != 200:
                warnings.warn(f"Failed to create issue: {response.text}")
                return None
            
            # Parse response
            data = response.json()
            if "errors" in data:
                warnings.warn(f"Failed to create issue: {data['errors']}")
                return None
            
            # Emit signal
            self.issue_created.emit(data["data"]["issueCreate"]["issue"])
            
            return data["data"]["issueCreate"]["issue"]
        except Exception as e:
            warnings.warn(f"Failed to create issue: {str(e)}")
            return None
    
    def get_teams(self):
        """
        Get all teams from Linear.
        
        Returns:
            list: List of teams if successful, empty list otherwise
        """
        if not self.api_key:
            warnings.warn("Linear API key not set")
            return []
        
        # Prepare GraphQL query
        query = """
        query Teams {
            teams {
                nodes {
                    id
                    name
                    key
                }
            }
        }
        """
        
        # Send request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json={"query": query}
            )
            
            # Check for errors
            if response.status_code != 200:
                warnings.warn(f"Failed to get teams: {response.text}")
                return []
            
            # Parse response
            data = response.json()
            if "errors" in data:
                warnings.warn(f"Failed to get teams: {data['errors']}")
                return []
            
            return data["data"]["teams"]["nodes"]
        except Exception as e:
            warnings.warn(f"Failed to get teams: {str(e)}")
            return []
    
    def get_states(self, team_id):
        """
        Get all states for a team from Linear.
        
        Args:
            team_id (str): Team ID
            
        Returns:
            list: List of states if successful, empty list otherwise
        """
        if not self.api_key:
            warnings.warn("Linear API key not set")
            return []
        
        # Prepare GraphQL query
        query = """
        query States($teamId: ID!) {
            team(id: $teamId) {
                states {
                    nodes {
                        id
                        name
                        color
                    }
                }
            }
        }
        """
        
        # Prepare variables
        variables = {
            "teamId": team_id
        }
        
        # Send request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json={
                    "query": query,
                    "variables": variables
                }
            )
            
            # Check for errors
            if response.status_code != 200:
                warnings.warn(f"Failed to get states: {response.text}")
                return []
            
            # Parse response
            data = response.json()
            if "errors" in data:
                warnings.warn(f"Failed to get states: {data['errors']}")
                return []
            
            return data["data"]["team"]["states"]["nodes"]
        except Exception as e:
            warnings.warn(f"Failed to get states: {str(e)}")
            return []
    
    def get_templates(self):
        """
        Get all Linear issue templates.
        
        Returns:
            list: List of templates
        """
        return self.settings.get("templates", [])
    
    def add_template(self, name, content):
        """
        Add a new Linear issue template.
        
        Args:
            name (str): Template name
            content (str): Template content
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            templates = self.settings.get("templates", [])
            templates.append({
                "name": name,
                "content": content
            })
            self.settings["templates"] = templates
            self.save_settings()
            return True
        except Exception as e:
            warnings.warn(f"Failed to add template: {str(e)}")
            return False
    
    def update_template(self, index, name, content):
        """
        Update an existing Linear issue template.
        
        Args:
            index (int): Index of the template to update
            name (str): Updated template name
            content (str): Updated template content
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            templates = self.settings.get("templates", [])
            if 0 <= index < len(templates):
                templates[index] = {
                    "name": name,
                    "content": content
                }
                self.settings["templates"] = templates
                self.save_settings()
                return True
            return False
        except Exception as e:
            warnings.warn(f"Failed to update template: {str(e)}")
            return False
    
    def remove_template(self, index):
        """
        Remove a Linear issue template.
        
        Args:
            index (int): Index of the template to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            templates = self.settings.get("templates", [])
            if 0 <= index < len(templates):
                templates.pop(index)
                self.settings["templates"] = templates
                self.save_settings()
                return True
            return False
        except Exception as e:
            warnings.warn(f"Failed to remove template: {str(e)}")
            return False
    
    def set_default_team(self, team_id):
        """
        Set the default team ID.
        
        Args:
            team_id (str): Team ID
        """
        self.settings["default_team_id"] = team_id
        self.save_settings()
    
    def set_default_state(self, state_id):
        """
        Set the default state ID.
        
        Args:
            state_id (str): State ID
        """
        self.settings["default_state_id"] = state_id
        self.save_settings()
    
    def set_default_template(self, template_name):
        """
        Set the default template name.
        
        Args:
            template_name (str): Template name
        """
        self.settings["default_template"] = template_name
        self.save_settings()
    
    def get_default_template(self):
        """
        Get the default template.
        
        Returns:
            dict: Template dictionary, or None if not found
        """
        template_name = self.settings.get("default_template", "")
        if not template_name:
            return None
        
        templates = self.settings.get("templates", [])
        for template in templates:
            if template["name"] == template_name:
                return template
        
        return None
        
    def cleanup(self):
        """
        Clean up resources used by the Linear integration.
        This method is called when the plugin is being unloaded.
        """
        try:
            # Close any open connections or resources
            logger.info("Cleaning up Linear integration")
            
            # Clear any cached data
            self.issues = {}
            self.teams = {}
            self.projects = {}
            
            # Cancel any pending operations
            if hasattr(self, 'pending_operations'):
                for op in self.pending_operations:
                    if hasattr(op, 'cancel') and callable(op.cancel):
                        op.cancel()
                self.pending_operations = []
            
            logger.info("Linear integration cleanup completed")
        except Exception as e:
            logger.error(f"Error during Linear integration cleanup: {e}", exc_info=True)
