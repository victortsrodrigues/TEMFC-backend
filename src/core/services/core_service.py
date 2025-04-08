import logging
import time

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
                "Iniciando processamento", 
                0, 
                "in_progress"
            )
        # Step 1: Retrieve data from CNES
        csv_input = self._retrieve_data_from_cnes(body, request_id)
        
        # Step 2 & 3: Process data with validator and data processor
        valid_months = self._process_data(csv_input, self._overall_result, body, request_id)
        
        if request_id:
                sse_manager.publish_progress(
                    request_id, 
                    3,
                    "Verificação finalizada com sucesso!",
                    100,
                    "completed"
                )
        
        time.sleep(2) # Simulate some processing time
        
        return valid_months

    def get_result_details(self):
        return self._overall_result
    
    def _retrieve_data_from_cnes(self, body, request_id=None):
        try:
            # Step 1: Retrieve data from CNES
            if request_id:
                sse_manager.publish_progress(
                    request_id, 
                    1, 
                    "Acessando histórico profissional no CNES", 
                    35, 
                    "in_progress"
                )
            
            csv_input = self.csv_scraper.get_csv_data(body, request_id)

            if not csv_input:
                # if request_id:
                #     sse_manager.publish_progress(
                #         request_id, 
                #         1, 
                #         "No data found for the provided credentials", 
                #         100, 
                #         "error"
                #     )
                raise NotFoundError("Profissional não encontrado no CNES")
                if request_id:
                    sse_manager.publish_progress(
                        request_id, 
                        1, 
                        "No data found for the provided credentials", 
                        100, 
                        "error"
                    )        

            if request_id:
                sse_manager.publish_progress(
                    request_id, 
                    1, 
                    "Histórico profissional acessado com sucesso!", 
                    100, 
                    "completed"
                )
                        
            return csv_input

        except CSVScrapingError as e:
            logging.error(f"CSV scraping error: {e.message}")
            # if request_id:
            #     sse_manager.publish_progress(
            #         request_id, 
            #         1, 
            #         f"{e.message}", 
            #         100, 
            #         "error"
            #     )
            raise NotFoundError(
                "Erro ao acessar o histórico profissional no CNES",
                {"source": "data_retrieval", "details": e.details}
            )
        except Exception as e:
            logging.error(f"Unexpected error in data retrieval: {str(e)}")
            # if request_id:
            #     sse_manager.publish_progress(
            #         request_id, 
            #         1, 
            #         f"Unexpected error retrieving data: {str(e)}", 
            #         100, 
            #         "error"
            #     )
            raise NotFoundError(
                "Profissional não encontrado no CNES",
                {"source": "data_retrieval", "details": str(e)},
            )
        
        
    def _process_data(self, csv_input, overall_result, body, request_id=None):
        try:
            # Step 2: Validate establishments
            if request_id:
                sse_manager.publish_progress(
                    request_id, 
                    2, 
                    "Verificando atuação em APS", 
                    30, 
                    "in_progress"
                )
            
            # Process the data using data_processor which will handle Step 2 & 3
            return self.data_processor.process_csv(csv_input, overall_result, body, request_id)
            
        except (DataProcessingError, EstablishmentValidationError, ScrapingError) as e:
            # Send error progress via SSE
            # if request_id:
            #     sse_manager.publish_progress(
            #         request_id, 
            #         2, 
            #         f"Error during processing: {e.message}", 
            #         100, 
            #         "error"
            #     )
            # Re-raise specific exceptions
            raise
        except DatabaseError as db_error:
            # Send database error progress via SSE
            # if request_id:
            #     sse_manager.publish_progress(
            #         request_id, 
            #         2, 
            #         f"Database service unavailable: {db_error.message}", 
            #         100, 
            #         "error"
            #     )
            # Convert DatabaseError to ExternalServiceError for API response
            logging.error(f"Database error during processing: {str(db_error)}")
            raise ExternalServiceError(
                "Banco de dados indisponível",
                {"source": "database", "details": db_error.details}
            )
        except Exception as e:
            # Send general error progress via SSE
            # if request_id:
            #     sse_manager.publish_progress(
            #         request_id, 
            #         2, 
            #         f"Error processing data: {str(e)}", 
            #         100, 
            #         "error"
            #     )
            # Convert any other exceptions to DataProcessingError
            logging.error(f"Data processing error: {str(e)}")
            raise DataProcessingError(
                "Erro ao processar os dados do profissional", {"reason": str(e)}
            )
