from flask import Flask
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from errors.base_error import BaseError
from core.services.core_service import Services
from utils.sse_manager import sse_manager


def create_app(config=None):
    """
    Application factory function that creates and configures the Flask app.
    
    Args:
        config: Configuration object or dictionary
        
    Returns:
        Flask application instance
    """
    # Initialize Flask application
    app = Flask(__name__)
    
    # Apply configuration if provided
    if config:
        app.config.from_mapping(config)
    
    # Enable CORS with broader settings for SSE
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Initialize application components
    app.services = Services()
    app.sse_manager = sse_manager
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register routes
    register_routes(app)
    
    
    return app


def register_error_handlers(app):
    """Register error handlers for the Flask application."""
    
    @app.errorhandler(BaseError)
    def handle_api_error(error):
        """
        Handle custom API errors.
        
        Args:
            error: The BaseError instance.
        
        Returns:
            Response: JSON response with error details and status code.
        """
        from flask import jsonify
        
        response = {
            "error": error.message,
            "status_code": error.status_code
        }
        if error.details:
            response["details"] = error.details
        return jsonify(response), error.status_code
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """
        Handle HTTP exceptions.
        
        Args:
            error: The HTTPException instance.
        
        Returns:
            Response: JSON response with error details and status code.
        """
        from flask import jsonify
        
        response = {
            "error": error.description,
            "status_code": error.code
        }
        return jsonify(response), error.code


def register_routes(app):
    """Register routes for the Flask application."""
    from routes.health import health_bp
    from routes.events import events_bp
    from routes.processing import processing_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(processing_bp)
