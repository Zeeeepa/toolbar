#!/usr/bin/env python3
"""
Command-line interface for the Toolbar application.
This module provides a simple CLI entry point for the Toolbar application.
"""

import sys
import argparse
from Toolbar.main import main

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Toolbar - A modular taskbar application with plugin support")
    parser.add_argument('--version', action='store_true', help='Show version information')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', type=str, help='Path to custom configuration file')
    return parser.parse_args()

def cli_main():
    """Command-line entry point for the Toolbar application."""
    args = parse_args()
    
    if args.version:
        from Toolbar import __version__
        print(f"Toolbar version {__version__}")
        return 0
    
    # Pass any command-line arguments to the main function
    # by modifying sys.argv
    if args.debug:
        sys.argv.append('--debug')
    
    if args.config:
        sys.argv.extend(['--config', args.config])
    
    # Call the main function
    return main()

if __name__ == "__main__":
    sys.exit(cli_main())
