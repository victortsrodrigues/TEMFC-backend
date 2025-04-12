import logging
from flask import Blueprint, jsonify
from repositories.establishment_repository import EstablishmentRepository

# Create a Blueprint for health-related routes
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the API and database connectivity.

    Returns:
        Response: JSON response with health status.
    """
    try:
        # Check database connectivity
        repo = EstablishmentRepository()
        repo.ping()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        logging.error(f"Database connectivity check failed: {str(e)}")
        return jsonify({"status": "unhealthy", "database": "disconnected", "error": str(e)}), 500