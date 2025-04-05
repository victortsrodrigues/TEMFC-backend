import logging
import traceback

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from core.services.core_service import Services
from errors.base_error import BaseError
from errors.validation_error import ValidationError
from schemas.validate_schemas import ValidateSchema, PydanticValidationError 


# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS for all domains on all routes

# Initialize application components
services = Services()

# Error handler for API errors
@app.errorhandler(BaseError)
def handle_api_error(error):
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
    response = {
        "error": error.description,
        "status_code": error.code
    }
    return jsonify(response), error.code


# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"}), 200


# Main processing endpoint
@app.route('/', methods=['POST'])
def process_data():
    """Process data from CPF and name"""
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
            raise ValidationError("Invalid body", details=errors)


        body = {
            "cpf": request_data.cpf,
            "name": request_data.name
        }
        
        # Run services
        valid_months = services.run_services(body)
        
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
        
        return jsonify(result), 200
    
    except BaseError as e:
        raise e
    
    except Exception as e:
        logging.error(f"Unexpected error in process_data: {str(e)}\n{traceback.format_exc()}")
        raise BaseError(f"Processing failed: {str(e)}", 500)

def run_api(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask API server"""
    app.run(host=host, port=port, debug=debug)