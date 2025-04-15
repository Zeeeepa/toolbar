#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import platform
import logging
import argparse
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("toolkit-installer")

def check_python_version():
    """Check if Python version is compatible."""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        logger.error(f"Python {required_version[0]}.{required_version[1]} or higher is required.")
        logger.error(f"Current version: {current_version[0]}.{current_version[1]}")
        return False
    
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ["PyQt5", "python-dotenv", "appdirs"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.warning(f"Missing required packages: {', '.join(missing_packages)}")
        return False, missing_packages
    
    return True, []

def install_dependencies(packages):
    """Install required dependencies."""
    logger.info(f"Installing required packages: {', '.join(packages)}")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        logger.info("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing dependencies: {e}")
        return False

def install_toolkit(dev_mode=False):
    """Install the toolkit package."""
    logger.info("Installing toolkit package...")
    
    try:
        if dev_mode:
            # Install in development mode
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
            logger.info("Toolkit installed in development mode.")
        else:
            # Install normally
            subprocess.check_call([sys.executable, "-m", "pip", "install", "."])
            logger.info("Toolkit installed successfully.")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing toolkit: {e}")
        return False

def create_desktop_shortcut():
    """Create a desktop shortcut for the toolkit."""
    logger.info("Creating desktop shortcut...")
    
    try:
        home_dir = Path.home()
        desktop_dir = home_dir / "Desktop"
        
        if not desktop_dir.exists():
            logger.warning("Desktop directory not found. Skipping shortcut creation.")
            return False
        
        if platform.system() == "Windows":
            # Create Windows shortcut
            shortcut_path = desktop_dir / "Toolkit.lnk"
            
            # Use PowerShell to create shortcut
            ps_command = f"""
            $WshShell = New-Object -comObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
            $Shortcut.TargetPath = "{sys.executable}"
            $Shortcut.Arguments = "-m toolkit.toolbar.main"
            $Shortcut.WorkingDirectory = "{os.getcwd()}"
            $Shortcut.Description = "Toolkit Taskbar"
            $Shortcut.Save()
            """
            
            subprocess.run(["powershell", "-Command", ps_command], check=True)
            
        elif platform.system() == "Linux":
            # Create Linux .desktop file
            desktop_file = desktop_dir / "toolkit.desktop"
            
            with open(desktop_file, "w") as f:
                f.write(f"""[Desktop Entry]
Type=Application
Name=Toolkit Taskbar
Comment=Toolkit Taskbar Application
Exec={sys.executable} -m toolkit.toolbar.main
Terminal=false
Categories=Utility;
""")
            
            # Make it executable
            os.chmod(desktop_file, 0o755)
            
        elif platform.system() == "Darwin":  # macOS
            # Create macOS .command file
            command_file = desktop_dir / "Toolkit.command"
            
            with open(command_file, "w") as f:
                f.write(f"""#!/bin/bash
{sys.executable} -m toolkit.toolbar.main
""")
            
            # Make it executable
            os.chmod(command_file, 0o755)
        
        logger.info("Desktop shortcut created successfully.")
        return True
    except Exception as e:
        logger.error(f"Error creating desktop shortcut: {e}")
        return False

def setup_autostart():
    """Set up the toolkit to start automatically on system boot."""
    logger.info("Setting up autostart...")
    
    try:
        if platform.system() == "Windows":
            # Set up Windows autostart
            startup_dir = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            
            if not startup_dir.exists():
                startup_dir.mkdir(parents=True, exist_ok=True)
            
            startup_file = startup_dir / "Toolkit.bat"
            
            with open(startup_file, "w") as f:
                f.write(f"""@echo off
start "" "{sys.executable}" -m toolkit.toolbar.main
""")
            
        elif platform.system() == "Linux":
            # Set up Linux autostart
            autostart_dir = Path.home() / ".config" / "autostart"
            
            if not autostart_dir.exists():
                autostart_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = autostart_dir / "toolkit.desktop"
            
            with open(desktop_file, "w") as f:
                f.write(f"""[Desktop Entry]
Type=Application
Name=Toolkit Taskbar
Comment=Toolkit Taskbar Application
Exec={sys.executable} -m toolkit.toolbar.main
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
""")
            
            # Make it executable
            os.chmod(desktop_file, 0o755)
            
        elif platform.system() == "Darwin":  # macOS
            # Set up macOS autostart
            launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
            
            if not launch_agents_dir.exists():
                launch_agents_dir.mkdir(parents=True, exist_ok=True)
            
            plist_file = launch_agents_dir / "com.zeeeepa.toolkit.plist"
            
            with open(plist_file, "w") as f:
                f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.zeeeepa.toolkit</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>-m</string>
        <string>toolkit.toolbar.main</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
""")
        
        logger.info("Autostart setup successfully.")
        return True
    except Exception as e:
        logger.error(f"Error setting up autostart: {e}")
        return False

def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(description="Install the Toolkit Taskbar application.")
    parser.add_argument("--dev", action="store_true", help="Install in development mode")
    parser.add_argument("--no-shortcut", action="store_true", help="Skip desktop shortcut creation")
    parser.add_argument("--no-autostart", action="store_true", help="Skip autostart setup")
    args = parser.parse_args()
    
    logger.info("Starting Toolkit installation...")
    
    # Check Python version
    if not check_python_version():
        logger.error("Installation aborted due to incompatible Python version.")
        return 1
    
    # Check and install dependencies
    deps_ok, missing_deps = check_dependencies()
    if not deps_ok:
        logger.info("Installing missing dependencies...")
        if not install_dependencies(missing_deps):
            logger.error("Installation aborted due to dependency installation failure.")
            return 1
    
    # Install toolkit
    if not install_toolkit(args.dev):
        logger.error("Installation aborted due to toolkit installation failure.")
        return 1
    
    # Create desktop shortcut
    if not args.no_shortcut:
        create_desktop_shortcut()
    
    # Set up autostart
    if not args.no_autostart:
        setup_autostart()
    
    logger.info("Toolkit installation completed successfully!")
    logger.info("You can now run the toolkit by executing 'toolbar' in your terminal or using the desktop shortcut.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
