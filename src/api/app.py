from flask import Flask, request, jsonify
import logging
from core.services.data_processor import DataProcessor
from core.services.establishment_validator import EstablishmentValidator
from repositories.establishment_repository import EstablishmentRepository
from interfaces.web_scraper import CNESScraper
from interfaces.report_generator import ReportGenerator
from interfaces.csv_scraper import CSVScraper
from flask_cors import CORS

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS for all domains on all routes

# Initialize application components
report_generator = ReportGenerator()
scraper = CNESScraper()
repo = EstablishmentRepository()
establishment_validator = EstablishmentValidator(repo, scraper)
data_processor = DataProcessor(establishment_validator)
csv_scraper = CSVScraper()

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/', methods=['POST'])
def process_data():
    """Process data from CPF and name"""
    try:
        # Get request data
        request_data = request.json
        
        # Validate input
        if not request_data:
            return jsonify({"error": "No request body provided"}), 400
        
        cpf = request_data.get('cpf')
        name = request_data.get('name')
        
        if not cpf and not name:
            return jsonify({"error": "Either CPF or name must be provided"}), 400
        
        # Prepare body for processing
        body = {
            "cpf": cpf,
            "name": name
        }
        
        # Process data
        overall_result = {}
        csv_input = csv_scraper.get_csv_data(body)
        
        if not csv_input:
            return jsonify({"error": "No data found for the provided credentials"}), 404
        
        valid_months = data_processor.process_csv(csv_input, overall_result, body)
        
        # Generate report for console (optional in API context)
        report_generator.report_terminal(body, valid_months)
        
        # Prepare API response
        result = {
            "name": body["name"],
            "valid_months": valid_months,
            "status": "ELIGIBLE" if valid_months >= 48 else "NOT ELIGIBLE",
            "pending_months": max(0, 48 - valid_months)
        }
        
        if overall_result and body["name"] in overall_result:
            details = overall_result[body["name"]]
            result["details"] = {
                "semesters_40": details["semesters_40"],
                "semesters_30": details["semesters_30"],
                "semesters_20": details["semesters_20"]
            }
        
        return jsonify(result), 200
    
    except Exception as e:
        logging.error(f"API error: {str(e)}")
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

def run_api(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask API server"""
    app.run(host=host, port=port, debug=debug)