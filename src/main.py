import logging
import time
import os
from config.settings import settings
from core.services.data_processor import DataProcessor
from core.services.establishment_validator import EstablishmentValidator
from repositories.establishment_repository import EstablishmentRepository
from interfaces.web_scraper import CNESScraper
from interfaces.report_generator import ReportGenerator

class Application:
    def __init__(self):
        self.report_generator = ReportGenerator()
        self.scraper = CNESScraper()
        self.repo = EstablishmentRepository()
        self.establishment_validator = EstablishmentValidator(self.repo, self.scraper)
        self.data_processor = DataProcessor(self.establishment_validator)

    def run(self):
        
        start_time = time.time()
        
        current_assets_dir = settings.ASSETS_DIR
        logging.info(f"Usando diretório: {current_assets_dir}")
        
        overall_result = {}

        try:
            with os.scandir(current_assets_dir) as entries:
                for entry in entries:
                    if entry.name.endswith('.csv'):
                        valid_months = self.data_processor.process_csv(entry.path, overall_result)
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