import sys
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolBar, QWidget, QVBoxLayout
from Toolbar.core.plugin_manager import PluginManager

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Toolbar")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Load plugins
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_plugins()
        
        # Add plugin widgets to toolbar
        for plugin_name, plugin in self.plugin_manager.plugins.items():
            widget = plugin.get_widget()
            toolbar.addWidget(widget)
            logger.info(f"Added plugin widget: {plugin_name}")

def main():
    logger.info("Starting Toolbar...")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
