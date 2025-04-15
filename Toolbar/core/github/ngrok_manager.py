import os
import json
import logging
import subprocess
import time
import threading
from typing import Dict, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class NgrokManager:
    """
    Manages ngrok tunnels for webhook server.
    """
    
    def __init__(self, auth_token: Optional[str] = None):
        """
        Initialize the ngrok manager.
        
        Args:
            auth_token (str, optional): Ngrok authentication token
        """
        self.auth_token = auth_token
        self.tunnel_url = None
        self.process = None
        self.tunnel_thread = None
        self.stop_tunnel_flag = threading.Event()
    
    def start_tunnel(self, port: int, options: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
        """
        Start an ngrok tunnel to the specified port.
        
        Args:
            port (int): Local port to tunnel to
            options (dict, optional): Additional ngrok options
            
        Returns:
            tuple: (success, tunnel_url)
        """
        if self.process is not None:
            logger.warning("Ngrok tunnel already running")
            return True, self.tunnel_url
        
        # Set up ngrok command
        cmd = ["ngrok", "http", str(port)]
        
        # Add auth token if provided
        if self.auth_token:
            cmd.extend(["--authtoken", self.auth_token])
        
        # Add additional options
        if options:
            for key, value in options.items():
                cmd.extend([f"--{key}", str(value)])
        
        try:
            # Start ngrok process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Start thread to monitor ngrok output
            self.stop_tunnel_flag.clear()
            self.tunnel_thread = threading.Thread(target=self._monitor_tunnel)
            self.tunnel_thread.daemon = True
            self.tunnel_thread.start()
            
            # Wait for tunnel URL to be available
            start_time = time.time()
            while self.tunnel_url is None:
                if time.time() - start_time > 10:  # Timeout after 10 seconds
                    logger.error("Timed out waiting for ngrok tunnel URL")
                    self.stop_tunnel()
                    return False, None
                
                time.sleep(0.1)
            
            logger.info(f"Ngrok tunnel started: {self.tunnel_url}")
            return True, self.tunnel_url
        except Exception as e:
            logger.error(f"Error starting ngrok tunnel: {e}")
            return False, None
    
    def stop_tunnel(self) -> bool:
        """
        Stop the ngrok tunnel.
        
        Returns:
            bool: True if tunnel was stopped successfully, False otherwise
        """
        if self.process is None:
            logger.warning("No ngrok tunnel running")
            return True
        
        try:
            # Signal thread to stop
            self.stop_tunnel_flag.set()
            
            # Terminate process
            self.process.terminate()
            self.process.wait(timeout=5)
            
            # Clean up
            self.process = None
            self.tunnel_url = None
            
            if self.tunnel_thread is not None:
                self.tunnel_thread.join(timeout=1.0)
                self.tunnel_thread = None
            
            logger.info("Ngrok tunnel stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping ngrok tunnel: {e}")
            return False
    
    def _monitor_tunnel(self):
        """Monitor ngrok output to extract tunnel URL."""
        try:
            # Get ngrok API URL
            api_url = "http://localhost:4040/api/tunnels"
            
            # Poll API until tunnel is available
            while not self.stop_tunnel_flag.is_set():
                try:
                    # Use curl to get tunnel info
                    curl_process = subprocess.run(
                        ["curl", "-s", api_url],
                        capture_output=True,
                        text=True
                    )
                    
                    if curl_process.returncode == 0:
                        try:
                            tunnels = json.loads(curl_process.stdout)
                            
                            if "tunnels" in tunnels and tunnels["tunnels"]:
                                for tunnel in tunnels["tunnels"]:
                                    if tunnel["proto"] == "https":
                                        self.tunnel_url = tunnel["public_url"]
                                        return
                        except json.JSONDecodeError:
                            pass
                except Exception:
                    pass
                
                # Check if process is still running
                if self.process.poll() is not None:
                    logger.warning("Ngrok process terminated unexpectedly")
                    return
                
                # Wait before polling again
                time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error monitoring ngrok tunnel: {e}")
        finally:
            # Clean up if thread is stopping
            if self.stop_tunnel_flag.is_set() and self.process is not None:
                try:
                    self.process.terminate()
                    self.process = None
                except Exception:
                    pass
