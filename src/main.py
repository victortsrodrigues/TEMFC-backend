import logging
import time
import os
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
        
    def run(self):
        start_time = time.time()

        overall_result = {}

        body = {
            "cpf": "08060455417",
            "name": "PEDRO RODA DA SILVA NETO"
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
            # self.report_generator.report_file(overall_result)
            logging.info(f"Execution time: {time.time() - start_time:.2f}s")
    
if __name__ == "__main__":
    app = Application()
    app.run()