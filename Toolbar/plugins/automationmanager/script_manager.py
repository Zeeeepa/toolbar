import os
import subprocess
import json
import logging
import warnings
import platform
import sys

class ScriptManager:
    """
    Manages script execution and configuration.
    This class handles running scripts, editing them, and managing their metadata.
    """
    
    def __init__(self, config):
        """
        Initialize the script manager.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def run_script(self, path):
        """
        Run a script.
        
        Args:
            path (str): Path to the script
        """
        try:
            # Check if the script exists
            if not os.path.exists(path):
                warnings.warn(f"Script not found: {path}")
                return
            
            # Get the script extension
            _, ext = os.path.splitext(path)
            
            # Run the script based on its extension
            if ext.lower() == '.py':
                # Run Python script
                subprocess.Popen([sys.executable, path])
            elif ext.lower() == '.sh' and platform.system() != 'Windows':
                # Run shell script on non-Windows systems
                subprocess.Popen(['bash', path])
            elif ext.lower() == '.bat' and platform.system() == 'Windows':
                # Run batch script on Windows
                subprocess.Popen([path], shell=True)
            else:
                # Run as executable
                if platform.system() == 'Windows':
                    subprocess.Popen([path], shell=True)
                else:
                    subprocess.Popen([path])
        except Exception as e:
            self.logger.error(f"Error running script {path}: {e}")
            warnings.warn(f"Error running script: {e}")
    
    def edit_script(self, path):
        """
        Edit a script.
        
        Args:
            path (str): Path to the script
        """
        try:
            # Check if the script exists
            if not os.path.exists(path):
                warnings.warn(f"Script not found: {path}")
                return
            
            # Get the editor from configuration
            editor = self.config.get('scripts', 'editor', None)
            
            if editor:
                # Use the configured editor
                subprocess.Popen([editor, path])
            else:
                # Use the default system editor
                if platform.system() == 'Windows':
                    os.startfile(path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.Popen(['open', path])
                else:  # Linux and other Unix-like
                    subprocess.Popen(['xdg-open', path])
        except Exception as e:
            self.logger.error(f"Error editing script {path}: {e}")
            warnings.warn(f"Error editing script: {e}")
    
    def add_script(self, path, name, description=""):
        """
        Add a script to the configuration.
        
        Args:
            path (str): Path to the script
            name (str): Name of the script
            description (str, optional): Description of the script
        
        Returns:
            dict: Script data
        """
        try:
            # Create script data
            script_data = {
                'path': path,
                'name': name,
                'description': description
            }
            
            # Add to configuration
            scripts = self.config.get_scripts()
            scripts.append(script_data)
            self.config.set_scripts(scripts)
            
            return script_data
        except Exception as e:
            self.logger.error(f"Error adding script {path}: {e}")
            warnings.warn(f"Error adding script: {e}")
            return None
    
    def update_script_icon(self, path, icon_path):
        """
        Update the icon of a script.
        
        Args:
            path (str): Path to the script
            icon_path (str): Path to the icon
        """
        try:
            # Get scripts from configuration
            scripts = self.config.get_scripts()
            
            # Find the script
            for script in scripts:
                if script.get('path') == path:
                    # Update icon
                    script['icon'] = icon_path
                    break
            
            # Save changes
            self.config.set_scripts(scripts)
        except Exception as e:
            self.logger.error(f"Error updating script icon {path}: {e}")
            warnings.warn(f"Error updating script icon: {e}")
    
    def delete_script(self, path):
        """
        Delete a script from the configuration.
        
        Args:
            path (str): Path to the script
        """
        try:
            # Get scripts from configuration
            scripts = self.config.get_scripts()
            
            # Filter out the script to delete
            scripts = [s for s in scripts if s.get('path') != path]
            
            # Save changes
            self.config.set_scripts(scripts)
        except Exception as e:
            self.logger.error(f"Error deleting script {path}: {e}")
            warnings.warn(f"Error deleting script: {e}")
