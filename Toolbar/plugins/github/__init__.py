"""
GitHub integration plugin for the Toolbar application.
"""

import os
import logging
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget

logger = logging.getLogger(__name__)

class GitHubPlugin:
    def __init__(self):
        self._name = "GitHub Integration"
        self._icon = None
        self._config = None
        self._event_bus = None
        self._toolbar = None

    @property
    def name(self):
        return self._name

    def get_icon(self):
        return self._icon or QIcon()

    def initialize(self, config, event_bus, toolbar):
        self._config = config
        self._event_bus = event_bus
        self._toolbar = toolbar
        try:
            from .pr_handler import setup_pr_handler
            setup_pr_handler(self._event_bus)
        except ImportError:
            print("Could not initialize GitHub PR handler")
