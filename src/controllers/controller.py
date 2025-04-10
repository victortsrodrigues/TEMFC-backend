import logging
import traceback
import uuid

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from core.services.core_service import Services
from errors.base_error import BaseError
from errors.validation_error import ValidationError
from schemas.validate_schemas import ValidateSchema, PydanticValidationError 
from utils.sse_manager import sse_manager


# Initialize Flask application
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS with broader settings for SSE

# Initialize application components
services = Services()

# Error handler for API errors
@app.errorhandler(BaseError)
def handle_api_error(error):
    """
    Handle custom API errors.

    Args:
        error: The BaseError instance.

    Returns:
        Response: JSON response with error details and status code.
    """
    response = {
        "error": error.message,
        "status_code": error.status_code
    }
    if error.details:
        response["details"] = error.details
    return jsonify(response), error.status_code


# Error handler for HTTP exceptions
@app.errorhandler(HTTPException)
def handle_http_exception(error):
    """
    Handle HTTP exceptions.

    Args:
        error: The HTTPException instance.

    Returns:
        Response: JSON response with error details and status code.
    """
    response = {
        "error": error.description,
        "status_code": error.code
    }
    return jsonify(response), error.code


# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the API is running.

    Returns:
        Response: JSON response with health status.
    """
    return jsonify({"status": "healthy"}), 200


# SSE connection endpoint
@app.route('/events', methods=['GET'])
def events():
    """
    SSE endpoint to stream progress events to the client.

    Returns:
        Response: Flask response object with the event stream.
    """
    # Get the request_id from the query string, or create a new one
    request_id = request.args.get('request_id')
    
    if not request_id:
        # If no request_id is provided, create a new client
        request_id = sse_manager.create_client()
    elif request_id not in sse_manager.clients:
        # If the request_id doesn't exist yet, create it
        sse_manager.create_client(request_id)
    
    return sse_manager.stream(request_id)


# Main processing endpoint
@app.route('/', methods=['POST'])
def process_data():
    """
    Main endpoint to process professional data based on CPF and name.

    Returns:
        Response: JSON response with request ID and processing status.
    """
    try:
        # Validação com Pydantic
        try:
            request_data = ValidateSchema(**request.json)
        except PydanticValidationError as e:
            errors = {}
            for error in e.errors():
                field = error['loc'][0]
                msg = error['msg']
                errors[field] = msg
            raise ValidationError("Dados inválidos", details=errors)

        body = {
            "cpf": request_data.cpf,
            "name": request_data.name
        }
        
        # Generate a unique request ID for this processing job
        request_id = str(uuid.uuid4())
        sse_manager.create_client(request_id)
        
        # Include request_id in the response so the client can use it to connect to the events endpoint
        initial_response = {
            "request_id": request_id,
            "status": "processing",
            "message": "Processing started. Connect to /events?request_id={} for updates.".format(request_id)
        }
        
        # Start processing in a separate thread
        from threading import Thread
        
        def process_async():
            try:
                # Run services with SSE updates
                valid_months = services.run_services(body, request_id)
                
                # Prepare API response
                result = {
                    "name": body["name"],
                    "valid_months": valid_months,
                    "status": "ELIGIBLE" if valid_months >= 48 else "NOT ELIGIBLE",
                    "pending_months": max(0, 48 - valid_months)
                }
                
                if valid_months > 0 and body["name"] in services.get_result_details():
                    details = services.get_result_details()[body["name"]]
                    result["details"] = {
                        "semesters_40": details["semesters_40"],
                        "semesters_30": details["semesters_30"],
                        "semesters_20": details["semesters_20"]
                    }
                
                # Send the final result as an event
                sse_manager.publish_event(request_id, "result", result)
                sse_manager.publish_progress(request_id, 3, "Processo concluído!", 100, "completed")
                
            except BaseError as e:
                # Send error via SSE
                error_data = {
                    "error": e.message,
                    "status_code": e.status_code
                }
                if e.details:
                    error_data["details"] = e.details
                    
                sse_manager.publish_event(request_id, "error", error_data)
                sse_manager.publish_progress(request_id, 3, f"Error: {e.message}", None, "error")
                logging.error(f"Error in async processing: {e}")
                
            except Exception as e:
                # Send unexpected error via SSE
                error_msg = f"Processing failed: {str(e)}"
                sse_manager.publish_event(request_id, "error", {"error": error_msg, "status_code": 500})
                sse_manager.publish_progress(request_id, 3, "Erro inesperado", None, "error")
                logging.error(f"Unexpected error in async processing: {str(e)}\n{traceback.format_exc()}")
        
        # Start the processing thread
        Thread(target=process_async).start()
        
        # Return immediate response with request_id
        return jsonify(initial_response), 202  # 202 Accepted
    
    except BaseError as e:
        raise e
    
    except Exception as e:
        logging.error(f"Unexpected error in process_data: {str(e)}\n{traceback.format_exc()}")
        raise BaseError(f"O processo falhou: {str(e)}", 500)


def run_api(host='0.0.0.0', port=5000, debug=False):
    """
    Run the Flask API server.

    Args:
        host: Host address to bind the server.
        port: Port number to run the server.
        debug: Whether to run the server in debug mode.
    """
    app.run(host=host, port=port, debug=debug)
