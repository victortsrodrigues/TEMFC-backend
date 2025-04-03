import logging
import time
import os
import argparse
from config.settings import settings
from core.services.data_processor import DataProcessor
from core.services.establishment_validator import EstablishmentValidator
from repositories.establishment_repository import EstablishmentRepository
from interfaces.web_scraper import CNESScraper
from interfaces.report_generator import ReportGenerator
from interfaces.csv_scraper import CSVScraper

class Application:
    def __init__(self):
        self.report_generator = ReportGenerator()
        self.scraper = CNESScraper()
        self.repo = EstablishmentRepository()
        self.establishment_validator = EstablishmentValidator(self.repo, self.scraper)
        self.data_processor = DataProcessor(self.establishment_validator)
        self.csv_scraper = CSVScraper()
        
    def run(self, cpf=None, name=None):
        start_time = time.time()

        overall_result = {}

        body = {
            "cpf": cpf if cpf else "05713248356",
            "name": name if name else "LETICIA LIMA LUZ"
        }
        
        try:
            csv_input = self.csv_scraper.get_csv_data(body)
            valid_months = self.data_processor.process_csv(csv_input, overall_result, body)
            self.report_generator.report_terminal(body, valid_months)
        except Exception as e:
            logging.error(f"Processing failed: {e}")
        finally:
            if len(overall_result) == 0:
                logging.error("No data found.")
            logging.info(f"Execution time: {time.time() - start_time:.2f}s")
    
def run_script_mode(cpf=None, name=None):
    app = Application()
    app.run(cpf, name)

def run_api_mode(host='0.0.0.0', port=5000, debug=False):
    # Import here to avoid circular imports
    from api.app import run_api
    run_api(host, port, debug)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the professional data processor')
    parser.add_argument('--api', action='store_true', help='Run as API server')
    parser.add_argument('--host', default='0.0.0.0', help='API server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='API server port (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Run API server in debug mode')
    parser.add_argument('--cpf', help='CPF for script mode')
    parser.add_argument('--name', help='Name for script mode')
    
    args = parser.parse_args()
    
    args.api = True
    
    if args.api:
        run_api_mode(args.host, args.port, args.debug)
    else:
        run_script_mode(args.cpf, args.name)