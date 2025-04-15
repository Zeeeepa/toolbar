#!/usr/bin/env python3
"""
Configure GitHub and ngrok settings for the Toolbar application.
This script allows setting up the GitHub credentials and ngrok authentication token.
"""
import sys
import os
import getpass

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from Toolbar.core.config import Config
import requests

def test_github_credentials(username, token):
    """Test GitHub credentials to ensure they work."""
    if not username or not token:
        return False, "Username or token is empty"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # First, check if we can access user information
        user_response = requests.get("https://api.github.com/user", headers=headers)
        if user_response.status_code != 200:
            return False, f"Authentication failed: {user_response.status_code} - {user_response.json().get('message', 'Unknown error')}"
        
        user_data = user_response.json()
        login = user_data.get('login')
        
        # Check token scopes
        scopes = user_response.headers.get('X-OAuth-Scopes', '')
        required_scopes = ['repo', 'admin:repo_hook']
        missing_scopes = [scope for scope in required_scopes if scope not in scopes]
        
        if missing_scopes:
            return True, f"Authentication successful as {login}, but missing required scopes: {', '.join(missing_scopes)}\nPlease regenerate your token with these scopes."
        
        return True, f"Authentication successful! Logged in as {login} with all required scopes."
    except Exception as e:
        return False, f"Error testing credentials: {str(e)}"

def configure_github():
    """Configure GitHub credentials and ngrok token."""
    config = Config()
    
    print("\n===================================")
    print("===== GitHub Configuration =======")
    print("===================================")
    print("This script will help you configure GitHub and ngrok settings.\n")
    
    # Get current values
    current_username, current_token = config.get_github_credentials()
    current_ngrok_token = config.get_ngrok_auth_token()
    
    # GitHub credentials
    print(f"Current GitHub username: {current_username or 'Not set'}")
    username = input("Enter GitHub username (leave blank to keep current): ").strip()
    
    print(f"Current GitHub token: {'*****' if current_token else 'Not set'}")
    token = getpass.getpass("Enter GitHub token (leave blank to keep current): ").strip()
    
    # Update GitHub credentials if provided
    updated = False
    if username or token:
        # If only one is provided, use the current value for the other
        github_username = username or current_username
        github_token = token or current_token
        
        # Test the credentials before saving
        if github_username and github_token:
            print("\nTesting GitHub credentials...")
            success, message = test_github_credentials(github_username, github_token)
            print(message)
            
            if success:
                config.set_github_credentials(github_username, github_token)
                print("GitHub credentials updated and verified.")
                updated = True
            else:
                print("\nWARNING: The provided credentials failed verification.")
                if input("Save them anyway? (y/n): ").lower() == 'y':
                    config.set_github_credentials(github_username, github_token)
                    print("GitHub credentials updated (not verified).")
                    updated = True
                else:
                    print("GitHub credentials not updated.")
        else:
            print("\nWARNING: Username or token is empty. Both are required for GitHub integration.")
            if input("Continue with partial credentials? (y/n): ").lower() == 'y':
                config.set_github_credentials(github_username, github_token)
                print("Partial GitHub credentials updated.")
                updated = True
            else:
                print("GitHub credentials not updated.")
    
    # ngrok token
    print(f"\nCurrent ngrok auth token: {'*****' if current_ngrok_token else 'Not set'}")
    print("The ngrok token is required for GitHub webhook functionality.")
    print("Get your token from https://dashboard.ngrok.com/get-started/your-authtoken")
    ngrok_token = getpass.getpass("Enter ngrok auth token (leave blank to keep current): ").strip()
    
    # Update ngrok token if provided
    if ngrok_token:
        config.set_ngrok_auth_token(ngrok_token)
        print("ngrok auth token updated.")
        updated = True
    
    if updated:
        print("\nConfiguration saved. You may need to restart the Toolbar application for changes to take effect.")
    else:
        print("\nNo changes were made to the configuration.")
    
    print("\nTo use the GitHub integration with the toolbar:")
    print("1. Start the toolbar application: python run_toolbar.py")
    print("2. Click on the GitHub icon in the toolbar")
    print("3. Use the settings dialog to configure additional options")
    print("===================================")

if __name__ == "__main__":
    configure_github() 