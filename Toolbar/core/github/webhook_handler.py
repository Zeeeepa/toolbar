"""
GitHub webhook handler module.
This module provides tools for handling GitHub webhook events.
"""

import json
import logging
import threading
import http.server
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

class WebhookHandler:
    """
    Handles GitHub webhook events.
    """
    
    def __init__(self, github_monitor):
        """
        Initialize the webhook handler.
        
        Args:
            github_monitor: GitHub monitor instance
        """
        self.github_monitor = github_monitor
        self.server = None
        self.server_thread = None
        self.running = False
    
    def run_server(self, port=8000):
        """
        Run the webhook server.
        
        Args:
            port (int): Port to run the server on
        """
        if self.running:
            return
        
        try:
            # Create handler class with access to the GitHub monitor
            handler_class = self._create_handler_class()
            
            # Create server
            self.server = HTTPServer(('', port), handler_class)
            self.running = True
            
            logger.info(f"Starting webhook server on port {port}")
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"Error running webhook server: {e}")
            self.running = False
    
    def stop_server(self):
        """Stop the webhook server."""
        if self.server and self.running:
            self.running = False
            self.server.shutdown()
            logger.info("Webhook server stopped")
    
    def _create_handler_class(self):
        """
        Create a handler class with access to the GitHub monitor.
        
        Returns:
            class: Handler class
        """
        github_monitor = self.github_monitor
        
        class GitHubWebhookHandler(BaseHTTPRequestHandler):
            """HTTP request handler for GitHub webhooks."""
            
            def do_POST(self):
                """Handle POST requests from GitHub."""
                try:
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length).decode('utf-8')
                    
                    # Parse JSON data
                    data = json.loads(post_data)
                    
                    # Get event type
                    event_type = self.headers.get('X-GitHub-Event')
                    
                    # Process event
                    if event_type == 'ping':
                        logger.info("Received ping event from GitHub")
                        self.send_response(200)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(b'pong')
                    
                    elif event_type == 'push':
                        logger.info(f"Received push event from GitHub: {data.get('repository', {}).get('full_name')}")
                        self.send_response(200)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(b'OK')
                        
                        # Process push event
                        repo_full_name = data.get('repository', {}).get('full_name')
                        ref = data.get('ref')
                        sender = data.get('sender', {})
                        commits = data.get('commits', [])
                        
                        if repo_full_name and ref and sender:
                            github_monitor.handle_push_event(repo_full_name, ref, sender, commits)
                    
                    elif event_type == 'create':
                        logger.info(f"Received create event from GitHub: {data.get('repository', {}).get('full_name')}")
                        self.send_response(200)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(b'OK')
                        
                        # Process create event
                        repo_full_name = data.get('repository', {}).get('full_name')
                        ref = data.get('ref')
                        ref_type = data.get('ref_type')
                        sender = data.get('sender', {})
                        
                        if repo_full_name and ref and ref_type and sender:
                            github_monitor.handle_branch_event(repo_full_name, ref, ref_type, sender)
                    
                    elif event_type == 'release':
                        logger.info(f"Received release event from GitHub: {data.get('repository', {}).get('full_name')}")
                        self.send_response(200)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(b'OK')
                        
                        # Process release event
                        repo_full_name = data.get('repository', {}).get('full_name')
                        release = data.get('release', {})
                        sender = data.get('sender', {})
                        
                        if repo_full_name and release and sender:
                            github_monitor.handle_release_event(repo_full_name, release, sender)
                    
                    elif event_type == 'pull_request':
                        logger.info(f"Received pull request event from GitHub: {data.get('repository', {}).get('full_name')}")
                        self.send_response(200)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(b'OK')
                        
                        # Process pull request event
                        repo_full_name = data.get('repository', {}).get('full_name')
                        pull_request = data.get('pull_request', {})
                        action = data.get('action')
                        sender = data.get('sender', {})
                        
                        if repo_full_name and pull_request and action and sender:
                            github_monitor.handle_pull_request_event(repo_full_name, pull_request, action, sender)
                    
                    else:
                        logger.info(f"Received unsupported event from GitHub: {event_type}")
                        self.send_response(200)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(b'Unsupported event type')
                
                except Exception as e:
                    logger.error(f"Error handling webhook request: {e}")
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f"Error: {str(e)}".encode('utf-8'))
            
            def do_GET(self):
                """Handle GET requests."""
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'GitHub webhook server is running')
            
            def log_message(self, format, *args):
                """Override log_message to use our logger."""
                logger.info(f"{self.client_address[0]} - {format % args}")
        
        return GitHubWebhookHandler
