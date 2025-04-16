#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication

from Toolbar.core.config import Config
from Toolbar.core.enhanced_plugin_system import EnhancedPluginManager
from Toolbar.ui.toolbar_ui import ToolbarUI

logger = logging.getLogger(__name__)

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Main application entry point"""
    try:
        # Set up logging
        setup_logging()
        logger.info("Starting Toolbar application")

        # Load configuration
        config = Config()
        logger.info("Configuration loaded")

        # Initialize plugin manager
        plugin_manager = EnhancedPluginManager(config)
        plugin_manager.load_plugins()
        logger.info("Plugins loaded")

        # Create application
        app = QApplication(sys.argv)

        # Create and show toolbar
        try:
            toolbar = ToolbarUI(config, plugin_manager)
            toolbar.show()
            logger.info("Toolbar UI initialized and displayed")
        except Exception as e:
            logger.error("Failed to initialize toolbar UI: %s", str(e))
            logger.error(str(e), exc_info=True)
            return 1

        # Start event loop
        return app.exec_()

    except Exception as e:
        logger.error("Critical error: %s", str(e))
        logger.error(str(e), exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
