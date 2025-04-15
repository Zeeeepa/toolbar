import os
import json
import hmac
import hashlib
import logging
from typing import Dict, Any, Callable, Optional

# Configure logging
logger = logging.getLogger(__name__)

class WebhookHandler:
    """
    Handles GitHub webhook events.
    """
    
    def __init__(self, secret: Optional[str] = None):
        """
        Initialize the webhook handler.
        
        Args:
            secret (str, optional): Webhook secret for signature verification
        """
        self.secret = secret
        self.event_handlers = {}
    
    def register_event_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """
        Register a handler for a specific event type.
        
        Args:
            event_type (str): GitHub event type (e.g., 'push', 'pull_request')
            handler (callable): Function to handle the event
        """
        self.event_handlers[event_type] = handler
    
    def handle_webhook(self, event_type: str, payload: Dict[str, Any], signature: Optional[str] = None) -> bool:
        """
        Handle a webhook event.
        
        Args:
            event_type (str): GitHub event type
            payload (dict): Event payload
            signature (str, optional): GitHub signature for verification
            
        Returns:
            bool: True if handled successfully, False otherwise
        """
        # Verify signature if secret is set
        if self.secret and signature:
            if not self._verify_signature(payload, signature):
                logger.warning("Invalid webhook signature")
                return False
        
        # Handle the event
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type](payload)
                return True
            except Exception as e:
                logger.error(f"Error handling webhook event: {e}")
                return False
        else:
            logger.info(f"No handler registered for event type: {event_type}")
            return False
    
    def _verify_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Verify the webhook signature.
        
        Args:
            payload (dict): Event payload
            signature (str): GitHub signature
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not self.secret:
            return False
        
        # Convert payload to JSON string
        payload_str = json.dumps(payload, separators=(',', ':'))
        
        # Calculate expected signature
        mac = hmac.new(self.secret.encode('utf-8'), msg=payload_str.encode('utf-8'), digestmod=hashlib.sha256)
        expected_signature = f"sha256={mac.hexdigest()}"
        
        # Compare signatures
        return hmac.compare_digest(expected_signature, signature)
