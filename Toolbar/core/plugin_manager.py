from PyQt6.QtWidgets import QDialog
import importlib
import logging
import os

logger = logging.getLogger(__name__)

class PluginManager:
    def __init__(self):
        self.plugins = {}
        self.plugin_dir = os.path.join(os.path.dirname(__file__), '..', 'plugins')
        
    def load_plugins(self):
        """Load all plugins from the plugins directory"""
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            
        for plugin_name in os.listdir(self.plugin_dir):
            if plugin_name.startswith('__'):
                continue
                
            try:
                plugin_path = os.path.join(self.plugin_dir, plugin_name)
                if os.path.isdir(plugin_path):
                    self._load_plugin(plugin_name)
            except Exception as e:
                logger.error(f"Error loading plugin {plugin_name}: {str(e)}")
                logger.error(f"Failed to load plugin {plugin_name}: {str(e)}")
                
    def _load_plugin(self, plugin_name):
        """Load a single plugin by name"""
        try:
            module = importlib.import_module(f"Toolbar.plugins.{plugin_name}.plugin")
            plugin_class = getattr(module, f"{plugin_name.capitalize()}Plugin")
            plugin = plugin_class()
            self.plugins[plugin_name] = plugin
            logger.info(f"Successfully loaded plugin: {plugin_name}")
        except AttributeError:
            logger.error(f"No plugin class found in {plugin_name}")
            raise
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {str(e)}")
            raise
