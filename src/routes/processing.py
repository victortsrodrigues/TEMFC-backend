import logging
import traceback
import uuid
from threading import Thread

from flask import Blueprint, request, jsonify, current_app
from errors.base_error import BaseError
from errors.validation_error import ValidationError
from schemas.validate_schemas import ValidateSchema, PydanticValidationError

# Create a Blueprint for processing-related routes
processing_bp = Blueprint('processing', __name__)

@processing_bp.route('/', methods=['POST'])
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
        
        # Access shared components from app context
        sse_manager = current_app.sse_manager
        services = current_app.services
        
        # Create client for SSE updates
        sse_manager.create_client(request_id)
        
        initial_response = {
            "request_id": request_id,
            "status": "processing",
            "message": "Processing started. Connect to /events?request_id={} for updates.".format(request_id)
        }
        
        # Start processing in a separate thread
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
        
        thread = Thread(target=process_async)
        thread.daemon = True
        thread.start()
        
        # Return immediate response with request_id
        return jsonify(initial_response), 202
    
    except BaseError as e:
        raise e
    
    except Exception as e:
        logging.error(f"Unexpected error in process_data: {str(e)}\n{traceback.format_exc()}")
        raise BaseError(f"O processo falhou: {str(e)}", 500)