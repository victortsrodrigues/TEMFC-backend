from utils.cbo_checker import CBOChecker
from core.models.row_process_data import RowProcessData
from utils.date_parser import DateParser
from errors.establishment_validator_error import EstablishmentValidationError
from errors.database_error import DatabaseError
from errors.establishment_scraping_error import ScrapingError
from utils.sse_manager import sse_manager
import logging

class EstablishmentValidator:
    """
    Service for validating establishments using database and online resources.

    Attributes:
        repo: Repository for database operations.
        scraper: Scraper for online validation.
        logger: Logger for logging validation activities.
    """

    def __init__(self, repo, scraper):
        """
        Initializes the validator with a repository and scraper.

        Args:
            repo: Repository for database operations.
            scraper: Scraper for online validation.
        """
        self.repo = repo
        self.scraper = scraper
        self.logger = logging.getLogger(__name__)

    def check_establishment(self, csv_reader, request_id=None):
        """
        Validates establishments based on CSV data.

        Args:
            csv_reader: CSV reader object containing establishment data.
            request_id (str, optional): Request ID for progress tracking.

        Returns:
            list: List of valid CNES identifiers.

        Raises:
            EstablishmentValidationError: If validation fails.
            DatabaseError: If a database error occurs.
        """
        try:              
            unique_entries = self._get_unique_entries(csv_reader)
            if not unique_entries:
                self.logger.warning("No valid unique entries found in CSV data")
            
            valid_cnes = self._get_valid_cnes(unique_entries, request_id)
            
            if request_id:
                sse_manager.publish_progress(
                    request_id, 
                    2, 
                    f"Validados {len(valid_cnes)} estabelecimentos com sucesso", 
                    100, 
                    "completed"
                )
                
            return valid_cnes
        
        except EstablishmentValidationError:
            raise
        except DatabaseError:
            raise
        except ScrapingError:
            raise
        except Exception as e:
            self.logger.error(f"Error in check_establishment: {str(e)}")
            raise EstablishmentValidationError(
                "Erro ao validar estabelecimentos",
                {"reason": str(e)}
            )

    def _get_unique_entries(self, csv_reader):
        """
        Extracts unique entries from the CSV data.

        Args:
            csv_reader: CSV reader object containing establishment data.

        Returns:
            list: List of unique RowProcessData entries.

        Raises:
            EstablishmentValidationError: If processing fails.
        """
        unique_entries = []
        try:
            for line in csv_reader:
                try:
                    entry = self._create_entry(line)
                    if self._should_validate(entry, unique_entries):
                        unique_entries.append(entry)
                except Exception as e:
                    self.logger.warning(f"Skipping invalid line: {e}")
            return unique_entries
        except Exception as e:
            self.logger.error(f"Error processing CSV entries: {str(e)}")
            raise EstablishmentValidationError(
                "Erro ao processar dados do histórico",
                {"reason": str(e)}
            )

    def _get_valid_cnes(self, unique_entries, request_id=None):
        """
        Validates CNES identifiers from unique entries.

        Args:
            unique_entries (list): List of unique RowProcessData entries.
            request_id (str, optional): Request ID for progress tracking.

        Returns:
            list: List of valid CNES identifiers.

        Raises:
            DatabaseError: If a database error occurs.
        """
        valid_cnes = []
        validation_errors = []
        total_entries = len(unique_entries)
        
        for i, entry in enumerate(unique_entries):
            # Calculate progress percentage for SSE updates
            progress_percentage = 30 + int((i / total_entries) * 70) if total_entries > 0 else 50
            
            if entry.cnes not in valid_cnes:
                try:
                    db_result = self._validate_with_repo(entry)
                    
                    if db_result is True:
                        valid_cnes.append(entry.cnes)
                    elif db_result is None:
                        if request_id:
                            sse_manager.publish_progress(
                                request_id, 
                                2, 
                                "Verificando validade de estabelecimentos no CNES", 
                                progress_percentage, 
                                "in_progress"
                            )
                        self._validate_online(entry, valid_cnes)
                
                except DatabaseError as db_error:
                    self.logger.error(f"Database error validating CNES {entry.cnes}: {db_error}")
                    if request_id:
                        sse_manager.publish_progress(
                            request_id, 
                            2, 
                            f"Database error validating {entry.name} (CNES: {entry.cnes})", 
                            progress_percentage, 
                            "in_progress"
                        )
                    raise
                except ScrapingError:
                    raise
                except Exception as e:
                    validation_errors.append({
                        "cnes": entry.cnes, 
                        "name": entry.name,
                        "reason": str(e)
                    })
                    self.logger.error(f"Failed to validate CNES {entry.cnes}: {e}")
                    if request_id:
                        sse_manager.publish_progress(
                            request_id, 
                            2, 
                            f"Failed to validate {entry.name} (CNES: {entry.cnes}): {str(e)}", 
                            progress_percentage, 
                            "in_progress"
                        )
                    continue
        
        if validation_errors:
            self.logger.warning(f"Validation errors occurred: {validation_errors}")
        
        return valid_cnes

    
    def _validate_with_repo(self, entry):
        """
        Validates an entry using the repository.

        Args:
            entry (RowProcessData): Entry to validate.

        Returns:
            bool or None: Validation result from the repository.
        """
        return self.repo.check_establishment(entry.ibge + entry.cnes)
    
    
    def _validate_online(self, entry, valid_cnes):
        """
        Validates an entry using online resources.

        Args:
            entry (RowProcessData): Entry to validate.
            valid_cnes (list): List of valid CNES identifiers to update.
        """
        online_validation_success = self.scraper.validate_online(entry.cnes, entry.name)
        if online_validation_success:
            valid_cnes.append(entry.cnes)
    
    
    def _create_entry(self, line) -> RowProcessData:
        """
        Creates a RowProcessData object from a CSV line.

        Args:
            line (dict): Dictionary representing a CSV row.

        Returns:
            RowProcessData: Parsed data object.

        Raises:
            KeyError: If a required field is missing.
            ValueError: If a field has an invalid format.
        """
        try:
            cnes = line["CNES"]
            while len(cnes) < 7:
                cnes = "0" + cnes
            
            comp_value = DateParser.format_yyyymm_to_mm_yyyy(line["COMP."])
            
            return RowProcessData(
                cnes=cnes,
                ibge=line["IBGE"],
                name=line["ESTABELECIMENTO"],
                chs_amb=float(line["CHS AMB."]),
                cbo_desc=line["DESCRICAO CBO"],
                comp_value=comp_value
            )
        except KeyError as e:
            raise KeyError(f"Faltando o campo: {e}")
        except ValueError:
            raise ValueError

    def _should_validate(self, entry, unique_entries):
        """
        Determines if an entry should be validated.

        Args:
            entry (RowProcessData): Entry to check.
            unique_entries (list): List of already processed entries.

        Returns:
            bool: True if the entry should be validated, False otherwise.
        """
        return entry.chs_amb >= 10 and (
            CBOChecker.contains_clinico_terms(entry.cbo_desc) or 
            CBOChecker.contains_generalista_terms(entry.cbo_desc)
        ) and entry.cnes not in [e.cnes for e in unique_entries]
