import os
import json
import warnings
import dotenv

# Global configuration instance
_config_instance = None

def get_config_instance():
    """
    Get the global configuration instance.
    Creates one if it doesn't exist yet.
    
    Returns:
        Config: The global configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

class Config:
    """
    Centralized configuration management for the toolkit application.
    Handles loading, saving, and accessing configuration settings.
    """
    def __init__(self, config_dir=None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir (str, optional): Directory to store configuration files.
                                       Defaults to the application directory.
        """
        # Load environment variables from .env file if it exists
        dotenv.load_dotenv(override=True)
        
        if config_dir is None:
            self.config_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.config_dir = config_dir
            
        self.scripts_folder = os.path.join(self.config_dir, "scripts")
        self.config_file = os.path.join(self.config_dir, "toolbar_config.json")
        self.github_credentials_file = os.path.join(self.config_dir, "github_credentials.json")
        
        # Ensure scripts folder exists
        if not os.path.exists(self.scripts_folder):
            os.makedirs(self.scripts_folder)
            
        # Initialize configuration with default values
        self.config = {
            'scripts': [],
            'github': {
                'username': os.getenv('GITHUB_USERNAME', ''),
                'token': os.getenv('GITHUB_TOKEN', ''),
                'pinned_projects': '[]',  # Add default empty list for pinned projects
                'webhook_enabled': False,
                'webhook_port': 8000,
                'ngrok_auth_token': os.getenv('NGROK_AUTH_TOKEN', '')
            },
            'ui': {
                'opacity': 1.0,
                'stay_on_top': True,
                'position': 'top',
                'center_images': True
            },
            'settings': {}  # Add a settings section for general settings
        }
        
        # Load configuration if it exists
        self.load_config()
        
        # Override with environment variables if they exist
        self._load_from_environment()
    
    def _load_from_environment(self):
        """Load configuration values from environment variables."""
        if os.getenv('GITHUB_USERNAME'):
            self.config['github']['username'] = os.getenv('GITHUB_USERNAME')
        if os.getenv('GITHUB_TOKEN'):
            self.config['github']['token'] = os.getenv('GITHUB_TOKEN')
        if os.getenv('NGROK_AUTH_TOKEN'):
            self.config['github']['ngrok_auth_token'] = os.getenv('NGROK_AUTH_TOKEN')
    
    def load_config(self):
        """Load configuration from the config file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Update config with loaded values, preserving defaults for missing keys
                    self._update_dict(self.config, loaded_config)
            except Exception as e:
                warnings.warn(f"Failed to load configuration: {str(e)}")
    
    def save_config(self):
        """Save current configuration to the config file."""
        try:
            # Create a copy to avoid saving sensitive information
            config_to_save = self._create_safe_config()
            
            with open(self.config_file, 'w') as f:
                json.dump(config_to_save, f, indent=4)
        except Exception as e:
            warnings.warn(f"Failed to save configuration: {str(e)}")
    
    def _create_safe_config(self):
        """Create a copy of the config without sensitive information."""
        config_copy = json.loads(json.dumps(self.config))
        
        # Replace sensitive values with placeholders if they exist in environment variables
        if os.getenv('GITHUB_TOKEN') and self.config['github']['token']:
            config_copy['github']['token'] = "*** STORED IN ENVIRONMENT VARIABLE ***"
        if os.getenv('NGROK_AUTH_TOKEN') and self.config['github']['ngrok_auth_token']:
            config_copy['github']['ngrok_auth_token'] = "*** STORED IN ENVIRONMENT VARIABLE ***"
            
        return config_copy
    
    def get_github_credentials(self):
        """Get GitHub credentials from config."""
        return self.config.get('github', {}).get('username', ''), self.config.get('github', {}).get('token', '')
    
    def set_github_credentials(self, username, token):
        """Set GitHub credentials in config."""
        if 'github' not in self.config:
            self.config['github'] = {}
        self.config['github']['username'] = username
        self.config['github']['token'] = token
        self.save_config()
        
        # Also set environment variables if possible
        if token:
            os.environ['GITHUB_TOKEN'] = token
        if username:
            os.environ['GITHUB_USERNAME'] = username
    
    def set_ngrok_auth_token(self, token):
        """Set the ngrok authentication token."""
        if 'github' not in self.config:
            self.config['github'] = {}
        self.config['github']['ngrok_auth_token'] = token
        self.save_config()
        
        # Also set environment variable if possible
        if token:
            os.environ['NGROK_AUTH_TOKEN'] = token
    
    def get_ngrok_auth_token(self):
        """Get the ngrok authentication token."""
        return self.config.get('github', {}).get('ngrok_auth_token', '')
    
    def get_scripts(self):
        """Get configured scripts."""
        return self.config.get('scripts', [])
    
    def add_script(self, script_data):
        """Add a script to the configuration."""
        self.config.get('scripts', []).append(script_data)
        self.save_config()
    
    def remove_script(self, script_path):
        """Remove a script from the configuration."""
        self.config['scripts'] = [s for s in self.config.get('scripts', []) if s.get('path') != script_path]
        self.save_config()
    
    def update_script(self, script_path, updated_data):
        """Update a script's configuration."""
        for script in self.config.get('scripts', []):
            if script.get('path') == script_path:
                script.update(updated_data)
                break
        self.save_config()
    
    def get_setting(self, key, default=None):
        """
        Get a setting value from the configuration.
        
        Args:
            key (str): Setting key
            default: Default value if setting doesn't exist
            
        Returns:
            The setting value or default if not found
        """
        return self.config.get('settings', {}).get(key, default)
    
    def set_setting(self, key, value):
        """
        Set a setting value in the configuration.
        
        Args:
            key (str): Setting key
            value: Setting value
        """
        if 'settings' not in self.config:
            self.config['settings'] = {}
        self.config['settings'][key] = value
        self.save_config()
    
    def get(self, section, key, default=None):
        """
        Get a value from a specific section in the configuration.
        
        Args:
            section (str): Configuration section
            key (str): Setting key
            default: Default value if setting doesn't exist
            
        Returns:
            The value or default if not found
        """
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section, key, value):
        """
        Set a value in a specific section in the configuration.
        
        Args:
            section (str): Configuration section
            key (str): Setting key
            value: Setting value
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save_config()
    
    def _update_dict(self, target, source):
        """
        Recursively update a dictionary with another dictionary's values.
        
        Args:
            target (dict): The dictionary to update
            source (dict): The dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict(target[key], value)
            else:
                target[key] = value
