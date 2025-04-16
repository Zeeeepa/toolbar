import os
import sys
import logging
import argparse
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from Toolbar.core.config import Config
from Toolbar.core.enhanced_plugin_system import EnhancedPluginManager
from Toolbar.ui.toolbar_ui import ToolbarUI

logger = logging.getLogger(__name__)

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Toolbar application')
    parser.add_argument('--config', help='Path to config file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    return parser.parse_args()

def main():
    """Main entry point for the Toolbar application."""
    try:
        # Parse command line arguments
        args = parse_args()

        # Setup logging
        setup_logging()
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        logger.info("Starting Toolbar application")

        # Load configuration
        config = Config(args.config if args.config else None)
        logger.info("Configuration loaded")

        # Create Qt application
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        # Initialize plugin manager
        plugin_manager = EnhancedPluginManager(config)
        plugin_manager.load_all_plugins()
        logger.info("Plugins loaded")

        # Create and show toolbar
        toolbar = ToolbarUI(config, plugin_manager)
        toolbar.show()
        logger.info("Toolbar UI initialized and displayed")

        # Start Qt event loop
        sys.exit(app.exec_())

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        logger.exception(e)
        sys.exit(1)

if __name__ == '__main__':
    main()
