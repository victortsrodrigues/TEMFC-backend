from flask import Blueprint, request, current_app

# Create a Blueprint for event-related routes
events_bp = Blueprint('events', __name__)

@events_bp.route('/events', methods=['GET'])
def events():
    """
    SSE endpoint to stream progress events to the client.

    Returns:
        Response: Flask response object with the event stream.
    """
    # Access the SSE manager from the app context
    sse_manager = current_app.sse_manager
    
    # Get the request_id from the query string, or create a new one
    request_id = request.args.get('request_id')
    
    if not request_id:
        # If no request_id is provided, create a new client
        request_id = sse_manager.create_client()
    elif request_id not in sse_manager.clients:
        # If the request_id doesn't exist yet, create it
        sse_manager.create_client(request_id)
    
    return sse_manager.stream(request_id)