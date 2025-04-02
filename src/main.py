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
            "cpf": "05713248356",
            "name": "LETICIA LIMA LUZ"
        }
        sample_csv = self.csv_scraper.get_csv_data(body)
        
        try:
            with os.scandir(settings.ASSETS_DIR) as entries:
                for entry in entries:
                    if entry.name.endswith('.csv'):
                        valid_months = self.data_processor.process_csv(sample_csv, overall_result)
                        self.report_generator.report_terminal(entry.path, valid_months)
        except Exception as e:
            logging.error(f"Processing failed: {e}")
        finally:
            if len(overall_result) == 0:
                logging.error("No .csv files found.")
            self.report_generator.report_file(overall_result)
            logging.info(f"Execution time: {time.time() - start_time:.2f}s")
    
if __name__ == "__main__":
    app = Application()
    app.run()