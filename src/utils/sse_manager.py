import logging
import json
import uuid
import time
from queue import Queue, Empty
from threading import Thread, Lock
from flask import Response

class SSEManager:
    """
    Manages Server-Sent Events (SSE) for real-time communication with clients.
    """

    def __init__(self, cleanup_interval=60, max_idle_time=120, event_ttl=3600):
        """
        Initialize the SSEManager instance.

        Args:
            cleanup_interval: Seconds between cleanup operations
            max_idle_time: Maximum seconds a client can be idle before being removed

        Attributes:
            clients (dict): Store active client connections.
            client_last_active (dict): Track when each client was last active.
            logger (Logger): Logger instance for logging events.
            _lock (Lock): Thread synchronization lock for client operations.
            max_idle_time (int): Maximum seconds a client can be idle.
            event_ttl (int): Maximum time to retain events before discarding.
        """
        self.clients = {}  
        self.client_last_active = {}  
        self.last_events = {}  
        self.logger = logging.getLogger(__name__)
        self._lock = Lock()
        self.max_idle_time = max_idle_time
        self.event_ttl = event_ttl
        
        # Start cleanup thread to periodically remove stale connections
        self._start_cleanup_thread(cleanup_interval)

    def _start_cleanup_thread(self, interval):
        """
        Start a background thread to clean up stale connections.
        
        Args:
            interval: Seconds between cleanup operations
        """
        def cleanup_task():
            while True:
                time.sleep(interval)
                self.cleanup_stale_clients()
        
        # Create daemon thread that won't prevent application exit
        cleanup_thread = Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
        self.logger.info(f"Started cleanup thread with interval: {interval}s")

    def create_client(self, request_id=None):
        """
        Create a new SSE client with a unique ID.

        Args:
            request_id: Optional request identifier.

        Returns:
            str: Client ID that can be used to publish events.
        """
        client_id = request_id or str(uuid.uuid4())
        
        with self._lock:
            # Limit queue size to prevent memory issues
            self.clients[client_id] = Queue(maxsize=100)
            self.client_last_active[client_id] = time.time()
            
        self.logger.info(f"Created new SSE client: {client_id}")
        return client_id
    
    def remove_client(self, client_id):
        """
        Remove a client by ID.

        Args:
            client_id: The ID of the client to remove.
        """
        with self._lock:
            if client_id in self.clients:
                del self.clients[client_id]
                
            if client_id in self.client_last_active:
                del self.client_last_active[client_id]
                
            if client_id in self.last_events:
                del self.last_events[client_id]
                self.logger.debug(f"Cleaned retained events for {client_id}")
                
        self.logger.info(f"Removed SSE client: {client_id}")
    
    def update_client_activity(self, client_id):
        """
        Update the last active timestamp for a client.
        
        Args:
            client_id: The ID of the client to update.
        """
        with self._lock:
            if client_id in self.client_last_active:
                self.client_last_active[client_id] = time.time()
    
    def cleanup_stale_clients(self):
        """
        Remove clients that have been inactive for longer than max_idle_time.
        """
        current_time = time.time()
        stale_clients = []
        expired_events = []
        
        with self._lock:
            # Identify stale clients
            stale_clients = [
                cid for cid, last_active in self.client_last_active.items()
                if current_time - last_active > self.max_idle_time
            ]

            # Clean expired events for active clients
            for cid, event in self.last_events.items():
                if current_time - event["timestamp"] > self.event_ttl:
                    expired_events.append(cid)
            
        # Remove each stale client
        for client_id in stale_clients:
            self.logger.info(f"Removing stale client: {client_id} (inactive for >{self.max_idle_time}s)")
            self.remove_client(client_id)

        # Remove expired events
        for client_id in expired_events:
            with self._lock:
                if client_id in self.last_events:
                    del self.last_events[client_id]
                    self.logger.debug(f"Removed expired event for {client_id}")
        
    def publish_event(self, client_id, event_type, data, retry=None):
        """
        Publish an event to a specific client.

        Args:
            client_id: The ID of the client to send the event to.
            event_type: The type of the event.
            data: The data to send.
            retry: Optional retry interval in milliseconds.
        """
        with self._lock:
            if client_id not in self.clients:
                self.logger.warning(f"Attempted to publish to non-existent client: {client_id}")
                return
            
            # Store critical events with timestamp
            if event_type in ("error", "result"):
                self.last_events[client_id] = {
                    "type": event_type,
                    "data": data,
                    "timestamp": time.time()
                }
                self.logger.debug(f"Stored critical event for {client_id}: {event_type}")
            
            # Format the event data according to SSE specification
            event_data = f"event: {event_type}\n"
            
            # Convert data to JSON if it's a dict
            if isinstance(data, dict):
                data = json.dumps(data)
            
            # Add data line(s) - handle multi-line data
            for line in data.split('\n'):
                event_data += f"data: {line}\n"
            
            # Add retry if specified
            if retry:
                event_data += f"retry: {retry}\n"
            
            # Empty line to end the event
            event_data += "\n"
            
            # Add the event to the client's queue
            try:
                # Use put_nowait with a timeout to avoid blocking indefinitely
                self.clients[client_id].put_nowait(event_data)
                # Update last active timestamp
                self.client_last_active[client_id] = time.time()
                self.logger.debug(f"Published event to client {client_id}: {event_type}")
            except:
                self.logger.warning(f"Queue full for client {client_id}, event dropped")
    
    def publish_progress(self, client_id, step, message, percentage=None, status="in_progress"):
        """
        Publish a progress update event.

        Args:
            client_id: The ID of the client to send the event to.
            step: The current processing step (1, 2, or 3).
            message: A description of the current activity.
            percentage: Optional completion percentage (0-100).
            status: Status of the step (in_progress, completed, error).
        """
        data = {
            "step": step,
            "message": message,
            "status": status
        }
        
        if percentage is not None:
            data["percentage"] = percentage
            
        self.publish_event(client_id, "progress", data)
    
    def stream(self, client_id):
        """
        Generate the SSE stream for a client.

        Args:
            client_id: The ID of the client to stream to.

        Returns:
            Response: A Flask response object with the event stream.
        """
        def generate():
            try:
                # Send initial connection established event
                yield "event: connected\ndata: {\"client_id\": \"" + client_id + "\"}\n\n"
                
                # Send retained event if available and fresh
                with self._lock:
                    retained = self.last_events.get(client_id)
                    if retained and (time.time() - retained["timestamp"] < self.event_ttl):
                        yield self._format_event(retained["type"], retained["data"])
                        self.logger.debug(f"Sent retained {retained['type']} event to {client_id}")
                
                # Keep the connection open and wait for events with heartbeat
                heartbeat_interval = 15 
                poll_interval = 1 
                time_since_heartbeat = 0
                
                while True:
                    try:
                        # Use get with timeout to prevent indefinite blocking
                        event = self.clients[client_id].get(timeout=poll_interval)
                        time_since_heartbeat = 0
                        self.update_client_activity(client_id)
                        yield event
                    except Empty:
                        # No event available, check if we need to send a heartbeat
                        time_since_heartbeat += poll_interval
                        if time_since_heartbeat >= heartbeat_interval:
                            yield ": heartbeat\n\n"
                            time_since_heartbeat = 0
                            self.update_client_activity(client_id)
            except GeneratorExit:
                self.logger.info(f"Client disconnected: {client_id}")
            except Exception as e:
                self.logger.error(f"Error in SSE stream for client {client_id}: {e}")
            finally:
                self.remove_client(client_id)
        
        return Response(generate(), mimetype="text/event-stream")

    def _format_event(self, event_type, data):
        """Helper to format events consistently"""
        if isinstance(data, dict):
            data = json.dumps(data)
        return f"event: {event_type}\ndata: {data}\n\n"

# Singleton instance with conservative defaults (1 hour retention)
sse_manager = SSEManager(
    cleanup_interval=300,       # 5 minutes
    max_idle_time=3600,         # 1 hour
    event_ttl=3600              # 1 hour
)