import logging
from core.services.data_processor import DataProcessor
from core.services.establishment_validator import EstablishmentValidator
from repositories.establishment_repository import EstablishmentRepository
from interfaces.web_scraper import CNESScraper
from interfaces.csv_scraper import CSVScraper
from errors.external_service_error import ExternalServiceError
from errors.not_found_error import NotFoundError
from errors.data_processing_error import DataProcessingError
from errors.establishment_validator_error import EstablishmentValidationError
from errors.establishment_scraping_error import ScrapingError
from errors.database_error import DatabaseError
from errors.csv_scraping_error import CSVScrapingError
from utils.sse_manager import sse_manager


class Services:
    def __init__(self):
        self.scraper = CNESScraper()
        self.repo = EstablishmentRepository()
        self.establishment_validator = EstablishmentValidator(self.repo, self.scraper)
        self.data_processor = DataProcessor(self.establishment_validator)
        self.csv_scraper = CSVScraper()
        self._overall_result = {}

    def run_services(self, body, request_id=None):
        # Emitting initial progress event
        if request_id:
            sse_manager.publish_progress(
                request_id, 
                1, 
                "Starting process", 
                0, 
                "in_progress"
            )
        
        # Step 1: Retrieve data from CNES
        if request_id:
            sse_manager.publish_progress(
                request_id, 
                1, 
                "Downloading Professional data from CNES website", 
                10, 
                "in_progress"
            )
        csv_input = self._retrieve_data_from_cnes(body, request_id)
        
        # Step 2 & 3: Process data with validator and data processor
        valid_months = self._process_data(csv_input, self._overall_result, body, request_id)
        
        return valid_months

    def get_result_details(self):
        return self._overall_result
    
    def _retrieve_data_from_cnes(self, body, request_id=None):
        try:
            if request_id:
                sse_manager.publish_progress(
                    request_id, 
                    1, 
                    "Accessing CNES database", 
                    20, 
                    "in_progress"
                )
            
            csv_input = self.csv_scraper.get_csv_data(body)

            if not csv_input:
                if request_id:
                    sse_manager.publish_progress(
                        request_id, 
                        1, 
                        "No data found for the provided credentials", 
                        100, 
                        "error"
                    )
                raise NotFoundError("No data found for the provided credentials")

            if request_id:
                sse_manager.publish_progress(
                    request_id, 
                    1, 
                    "Professional data downloaded successfully", 
                    100, 
                    "completed"
                )
            
            return csv_input

        except CSVScrapingError as e:
            logging.error(f"CSV scraping error: {e.message}")
            if request_id:
                sse_manager.publish_progress(
                    request_id, 
                    1, 
                    f"Error retrieving data: {e.message}", 
                    100, 
                    "error"
                )
            raise NotFoundError(
                "Failed to retrieve data from CNES",
                {"source": "data_retrieval", "details": e.details}
            )
        except Exception as e:
            logging.error(f"Unexpected error in data retrieval: {str(e)}")
            if request_id:
                sse_manager.publish_progress(
                    request_id, 
                    1, 
                    f"Unexpected error retrieving data: {str(e)}", 
                    100, 
                    "error"
                )
            raise NotFoundError(
                "Failed to retrieve data from CNES",
                {"source": "data_retrieval", "details": str(e)},
            )
        
        
    def _process_data(self, csv_input, overall_result, body, request_id=None):
        try:
            # Step 2: Validate establishments
            if request_id:
                sse_manager.publish_progress(
                    request_id, 
                    2, 
                    "Checking the validity of establishments", 
                    0, 
                    "in_progress"
                )
            
            # Process the data using data_processor which will handle Step 2 & 3
            return self.data_processor.process_csv(csv_input, overall_result, body, request_id)
            
        except (DataProcessingError, EstablishmentValidationError, ScrapingError) as e:
            # Send error progress via SSE
            if request_id:
                sse_manager.publish_progress(
                    request_id, 
                    2, 
                    f"Error during processing: {e.message}", 
                    100, 
                    "error"
                )
            # Re-raise specific exceptions
            raise
        except DatabaseError as db_error:
            # Send database error progress via SSE
            if request_id:
                sse_manager.publish_progress(
                    request_id, 
                    2, 
                    f"Database service unavailable: {db_error.message}", 
                    100, 
                    "error"
                )
            # Convert DatabaseError to ExternalServiceError for API response
            logging.error(f"Database error during processing: {str(db_error)}")
            raise ExternalServiceError(
                "Database service unavailable",
                {"source": "database", "details": db_error.details}
            )
        except Exception as e:
            # Send general error progress via SSE
            if request_id:
                sse_manager.publish_progress(
                    request_id, 
                    2, 
                    f"Error processing data: {str(e)}", 
                    100, 
                    "error"
                )
            # Convert any other exceptions to DataProcessingError
            logging.error(f"Data processing error: {str(e)}")
            raise DataProcessingError(
                "Failed to process professional data", {"reason": str(e)}
            )
