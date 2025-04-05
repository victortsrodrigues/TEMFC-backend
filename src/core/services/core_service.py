import logging
from core.services.data_processor import DataProcessor
from core.services.establishment_validator import EstablishmentValidator
from repositories.establishment_repository import EstablishmentRepository
from interfaces.web_scraper import CNESScraper
from interfaces.report_generator import ReportGenerator
from interfaces.csv_scraper import CSVScraper
from errors.external_service_error import ExternalServiceError
from errors.not_found_error import NotFoundError
from errors.data_processing_error import DataProcessingError
from errors.establishment_validator_error import EstablishmentValidationError
from errors.establishment_scraping_error import ScrapingError
from errors.database_error import DatabaseError


class Services:
    def __init__(self):
        self.report_generator = ReportGenerator()
        self.scraper = CNESScraper()
        self.repo = EstablishmentRepository()
        self.establishment_validator = EstablishmentValidator(self.repo, self.scraper)
        self.data_processor = DataProcessor(self.establishment_validator)
        self.csv_scraper = CSVScraper()
        self._overall_result = {}

    def run_services(self, body):
        csv_input = self._retrieve_data_from_cnes(body)
        valid_months = self._process_data(csv_input, self._overall_result, body)
        return valid_months

    def get_result_details(self):
        return self._overall_result
    
    def _retrieve_data_from_cnes(self, body):
        try:
            csv_input = self.csv_scraper.get_csv_data(body)
        except Exception as e:
            logging.error(f"CSV scraping error: {str(e)}")
            raise ExternalServiceError(
                "Failed to retrieve data from CNES",
                {"source": "data_retrieval", "details": str(e)},
            )

        if not csv_input:
            raise NotFoundError("No data found for the provided credentials")

        return csv_input

    def _process_data(self, csv_input, overall_result, body):
        try:
            return self.data_processor.process_csv(csv_input, overall_result, body)
        except (DataProcessingError, EstablishmentValidationError, ScrapingError):
            # Re-raise specific exceptions
            raise
        except DatabaseError as db_error:
            # Convert DatabaseError to ExternalServiceError for API response
            logging.error(f"Database error during processing: {str(db_error)}")
            raise ExternalServiceError(
                "Database service unavailable",
                {"source": "database", "details": db_error.details}
            )
        except Exception as e:
            # Convert any other exceptions to DataProcessingError
            logging.error(f"Data processing error: {str(e)}")
            raise DataProcessingError(
                "Failed to process professional data", {"reason": str(e)}
            )
