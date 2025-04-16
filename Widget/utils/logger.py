import logging
import sys
from typing import Optional

class WidgetLogger:
    """Custom logger for widget functionality"""
    def __init__(self, name: str = "WidgetLogger"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # Format
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
    
    def info(self, msg: str):
        """Log info message"""
        self.logger.info(msg)
    
    def error(self, msg: str):
        """Log error message"""
        self.logger.error(msg)
    
    def warning(self, msg: str):
        """Log warning message"""
        self.logger.warning(msg)
    
    def debug(self, msg: str):
        """Log debug message"""
        self.logger.debug(msg)
    
    def set_level(self, level: int):
        """Set logger level"""
        self.logger.setLevel(level)
    
    def add_file_handler(self, filepath: str, level: Optional[int] = None):
        """Add a file handler to the logger"""
        file_handler = logging.FileHandler(filepath)
        file_handler.setLevel(level or logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)

# Create global logger instance
logger = WidgetLogger()
