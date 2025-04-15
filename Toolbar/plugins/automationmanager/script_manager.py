import os
import sys
import subprocess
import warnings
import shutil

class ScriptManager:
    """
    Manages script operations including adding, running, editing, and deleting scripts.
    """
    def __init__(self, config):
        """
        Initialize the script manager.
        
        Args:
            config (Config): Application configuration
        """
        self.config = config
        self.scripts_folder = config.scripts_folder
        
        # Ensure scripts folder exists
        if not os.path.exists(self.scripts_folder):
            os.makedirs(self.scripts_folder)
    
    def get_scripts(self):
        """
        Get all configured scripts.
        
        Returns:
            list: List of script data dictionaries
        """
        return self.config.get_scripts()
    
    def add_script(self, file_path, script_name, icon_path=None):
        """
        Add a script to the toolbar.
        
        Args:
            file_path (str): Path to the script file
            script_name (str): Name to display for the script
            icon_path (str, optional): Path to the icon file
            
        Returns:
            dict: Script data dictionary
        """
        # Store original path
        original_path = os.path.abspath(file_path)
            
        # Copy script to scripts folder
        script_destination = os.path.join(self.scripts_folder, os.path.basename(file_path))
        try:
            with open(file_path, 'r') as src_file:
                content = src_file.read()
                
            with open(script_destination, 'w') as dest_file:
                dest_file.write(content)
        except Exception as e:
            warnings.warn(f"Failed to copy script: {str(e)}")
            return None
        
        # Create script data
        script_data = {
            'name': script_name,
            'path': script_destination,
            'original_path': original_path,
            'icon_path': icon_path
        }
        
        # Add to configuration
        self.config.add_script(script_data)
        
        return script_data
    
    def run_script(self, script_path, original_path=None):
        """
        Run a script.
        
        Args:
            script_path (str): Path to the script in the scripts folder
            original_path (str, optional): Original path of the script
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Normalize paths to avoid directory name issues
            if script_path:
                script_path = os.path.normpath(script_path)
            if original_path:
                original_path = os.path.normpath(original_path)
            
            # Get the directory of the original script
            working_dir = None
            script_to_run = None
            
            # Check if original file still exists and use it if possible
            if original_path and os.path.exists(original_path):
                script_to_run = original_path
                working_dir = os.path.dirname(original_path)
            else:
                # If original doesn't exist, run from the copied version in scripts folder
                script_to_run = script_path
                working_dir = os.path.dirname(script_path)
            
            # Ensure working directory exists
            if not os.path.exists(working_dir):
                working_dir = os.getcwd()
            
            # Run the script based on its extension
            if script_to_run.endswith('.py'):
                subprocess.Popen([sys.executable, script_to_run], cwd=working_dir)
            elif script_to_run.endswith('.bat'):
                if os.name == 'nt':  # Windows
                    subprocess.Popen([script_to_run], shell=True, cwd=working_dir)
                else:
                    warnings.warn("Batch files can only be run on Windows")
                    return False
            else:
                subprocess.Popen([script_to_run], cwd=working_dir)
            return True
        except Exception as e:
            warnings.warn(f"Failed to run script: {str(e)}")
            return False
    
    def edit_script(self, script_path):
        """
        Open a script in the default editor.
        
        Args:
            script_path (str): Path to the script
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Try to use default system editor
            if os.name == 'nt':  # Windows
                os.startfile(script_path)
            else:  # macOS and Linux
                subprocess.Popen(['xdg-open', script_path])
            return True
        except Exception as e:
            warnings.warn(f"Failed to open editor: {str(e)}")
            return False
    
    def delete_script(self, script_path, delete_file=False):
        """
        Delete a script from the toolbar.
        
        Args:
            script_path (str): Path to the script
            delete_file (bool, optional): Whether to delete the file as well
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Remove from configuration
        self.config.remove_script(script_path)
        
        # Delete file if requested
        if delete_file:
            try:
                os.remove(script_path)
            except Exception as e:
                warnings.warn(f"Failed to delete file: {str(e)}")
                return False
        
        return True
    
    def update_script_icon(self, script_path, icon_path):
        """
        Update a script's icon.
        
        Args:
            script_path (str): Path to the script
            icon_path (str): Path to the new icon
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.config.update_script(script_path, {'icon_path': icon_path})
            return True
        except Exception as e:
            warnings.warn(f"Failed to update script icon: {str(e)}")
            return False
