import logging
import json
import uuid
from queue import Queue
from threading import Thread
from flask import Response

class SSEManager:
    """
    Manages Server-Sent Events for the application.
    Provides methods to create event streams and publish events to clients.
    """
    def __init__(self):
        self.clients = {}  # Store active client connections
        self.logger = logging.getLogger(__name__)

    def create_client(self, request_id=None):
        """
        Create a new SSE client with a unique ID
        
        Args:
            request_id: Optional request identifier
            
        Returns:
            str: Client ID that can be used to publish events
        """
        client_id = request_id or str(uuid.uuid4())
        self.clients[client_id] = Queue()
        self.logger.info(f"Created new SSE client: {client_id}")
        return client_id
    
    def remove_client(self, client_id):
        """
        Remove a client by ID
        
        Args:
            client_id: The ID of the client to remove
        """
        if client_id in self.clients:
            del self.clients[client_id]
            self.logger.info(f"Removed SSE client: {client_id}")
    
    def publish_event(self, client_id, event_type, data, retry=None):
        """
        Publish an event to a specific client
        
        Args:
            client_id: The ID of the client to send the event to
            event_type: The type of the event
            data: The data to send
            retry: Optional retry interval in milliseconds
        """
        if client_id not in self.clients:
            self.logger.warning(f"Attempted to publish to non-existent client: {client_id}")
            return
        
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
        self.clients[client_id].put(event_data)
        self.logger.debug(f"Published event to client {client_id}: {event_type}")
    
    def publish_progress(self, client_id, step, message, percentage=None, status="in_progress"):
        """
        Publish a progress update event
        
        Args:
            client_id: The ID of the client to send the event to
            step: The current processing step (1, 2, or 3)
            message: A description of the current activity
            percentage: Optional completion percentage (0-100)
            status: Status of the step (in_progress, completed, error)
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
        Generate the SSE stream for a client
        
        Args:
            client_id: The ID of the client to stream to
            
        Returns:
            Response: A Flask response object with the event stream
        """
        def generate():
            try:
                # Send initial connection established event
                yield "event: connected\ndata: {\"client_id\": \"" + client_id + "\"}\n\n"
                
                # Keep the connection open and wait for events
                while True:
                    # This will block until an event is available
                    event = self.clients[client_id].get()
                    yield event
            except GeneratorExit:
                self.logger.info(f"Client disconnected: {client_id}")
                self.remove_client(client_id)
            except Exception as e:
                self.logger.error(f"Error in SSE stream for client {client_id}: {e}")
                self.remove_client(client_id)
        
        return Response(generate(), mimetype="text/event-stream")

# Create a singleton instance
sse_manager = SSEManager()
