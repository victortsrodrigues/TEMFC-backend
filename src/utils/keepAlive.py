import logging
import time
import threading
import requests
import os
from datetime import datetime

class KeepAlive:
    """
    Utility class to keep the application alive on platforms like Render
    by sending periodic health check requests.
    """
    
    def __init__(self, app_url=None, interval_minutes=14):
        """
        Initialize the KeepAlive service.
        
        Args:
            app_url: URL of the application to ping (defaults to environment variable)
            interval_minutes: Interval between pings in minutes
        """
        self.app_url = app_url or os.environ.get('APP_URL')
        self.interval_minutes = interval_minutes
        self.is_running = False
        self.thread = None
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """Start the keep-alive service in a background thread."""
        if not self.app_url:
            self.logger.warning("No APP_URL provided. Keep-alive service not started.")
            return
            
        if self.is_running:
            self.logger.info("Keep-alive service is already running.")
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self.logger.info(f"Keep-alive service started. Will ping {self.app_url}/health every {self.interval_minutes} minutes.")
    
    def stop(self):
        """Stop the keep-alive service."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1)
        self.logger.info("Keep-alive service stopped.")
    
    def _run(self):
        """Run the keep-alive loop."""
        while self.is_running:
            try:
                health_url = f"{self.app_url.rstrip('/')}/health"
                response = requests.get(health_url, timeout=10)
                
                if response.status_code == 200:
                    self.logger.info(f"Keep-alive ping successful at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    self.logger.warning(f"Keep-alive ping returned status code {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"Keep-alive ping failed: {str(e)}")
                
            # Sleep for the specified interval
            interval_seconds = self.interval_minutes * 60
            time.sleep(interval_seconds)


# Singleton instance
keep_alive = KeepAlive()
