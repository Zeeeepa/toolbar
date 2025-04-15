import json
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from http.server import HTTPServer, BaseHTTPRequestHandler
from logging import getLogger

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)

class WebhookHandler:
    """
    Handles GitHub webhook events.
    Processes incoming webhook payloads and triggers appropriate callbacks.
    """
    
    def __init__(self, port: int = 8000):
        """
        Initialize the webhook handler.
        
        Args:
            port: Port to listen on for webhook events
        """
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False
        self.event_handlers = {}  # Map of event types to handler functions
        
    def register_handler(self, event_type: str, handler_func: Callable[[Dict[str, Any]], None]):
        """
        Register a handler function for a specific event type.
        
        Args:
            event_type: GitHub event type (e.g., "pull_request", "push")
            handler_func: Function to call when this event is received
        """
        self.event_handlers[event_type] = handler_func
        logger.info(f"Registered handler for event type: {event_type}")
        
    def start_server(self) -> bool:
        """
        Start the webhook server.
        
        Returns:
            True if server started successfully, False otherwise
        """
        if self.running:
            logger.warning("Webhook server is already running")
            return True
            
        try:
            # Create a request handler with access to our event handlers
            handler_class = self._create_handler_class()
            
            # Create and start the server
            self.server = HTTPServer(('0.0.0.0', self.port), handler_class)
            self.running = True
            
            # Start server in a separate thread
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            logger.info(f"Webhook server started on port {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start webhook server: {e}")
            return False
    
    def stop_server(self) -> bool:
        """
        Stop the webhook server.
        
        Returns:
            True if server stopped successfully, False otherwise
        """
        if not self.running:
            logger.warning("Webhook server is not running")
            return True
            
        try:
            self.running = False
            if self.server:
                self.server.shutdown()
                self.server.server_close()
                logger.info("Webhook server stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop webhook server: {e}")
            return False
    
    def _create_handler_class(self):
        """
        Create a request handler class with access to our event handlers.
        
        Returns:
            A request handler class
        """
        event_handlers = self.event_handlers
        
        class GitHubWebhookHandler(BaseHTTPRequestHandler):
            """HTTP request handler for GitHub webhooks."""
            
            def do_POST(self):
                """Handle POST requests from GitHub."""
                content_length = int(self.headers.get('Content-Length', 0))
                payload_data = self.rfile.read(content_length)
                
                # Parse JSON payload
                try:
                    payload = json.loads(payload_data.decode('utf-8'))
                    
                    # Get event type from headers
                    event_type = self.headers.get('X-GitHub-Event')
                    
                    if event_type:
                        logger.info(f"Received webhook event: {event_type}")
                        
                        # Call appropriate handler if registered
                        if event_type in event_handlers:
                            try:
                                event_handlers[event_type](payload)
                            except Exception as e:
                                logger.error(f"Error in event handler for {event_type}: {e}")
                        else:
                            logger.warning(f"No handler registered for event type: {event_type}")
                    
                    # Send response
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'OK')
                except json.JSONDecodeError:
                    logger.error("Invalid JSON payload")
                    self.send_response(400)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Invalid JSON payload')
                except Exception as e:
                    logger.error(f"Error processing webhook: {e}")
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Internal server error')
            
            def do_GET(self):
                """Handle GET requests (for testing)."""
                if self.path == '/webhook':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'GitHub webhook server is running')
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Not found')
            
            def log_message(self, format, *args):
                """Override log_message to use our logger."""
                logger.info(f"{self.client_address[0]} - {format % args}")
        
        return GitHubWebhookHandler
