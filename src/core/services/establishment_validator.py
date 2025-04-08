from utils.cbo_checker import CBOChecker
from core.models.row_process_data import RowProcessData
from utils.date_parser import DateParser
from errors.establishment_validator_error import EstablishmentValidationError
from errors.database_error import DatabaseError
from utils.sse_manager import sse_manager
import logging

class EstablishmentValidator:
    def __init__(self, repo, scraper):
        self.repo = repo
        self.scraper = scraper
        self.logger = logging.getLogger(__name__)

    def check_establishment(self, csv_reader, request_id=None):
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
        except DatabaseError:
            # if request_id:
            #     sse_manager.publish_progress(
            #         request_id, 
            #         2, 
            #         "Database error during establishment validation", 
            #         100, 
            #         "error"
            #     )
            raise
        except Exception as e:
            # if request_id:
            #     sse_manager.publish_progress(
            #         request_id, 
            #         2, 
            #         f"Error validating establishments: {str(e)}", 
            #         100, 
            #         "error"
            #     )
            self.logger.error(f"Error in check_establishment: {str(e)}")
            raise EstablishmentValidationError(
                "Erro ao validar estabelecimentos",
                {"reason": str(e)}
            )

    def _get_unique_entries(self, csv_reader):
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
                        # Not found in database, try online validation
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
        return self.repo.check_establishment(entry.ibge + entry.cnes)
    
    
    def _validate_online(self, entry, valid_cnes):
        online_validation_success = self.scraper.validate_online(entry.cnes, entry.name)
        if online_validation_success:
            valid_cnes.append(entry.cnes)
    
    
    def _create_entry(self, line) -> RowProcessData:
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
        except ValueError as e:
            raise ValueError(f"Formato de dado inválido: {e}")

    def _should_validate(self, entry, unique_entries):
        return entry.chs_amb >= 10 and (
            CBOChecker.contains_clinico_terms(entry.cbo_desc) or 
            CBOChecker.contains_generalista_terms(entry.cbo_desc)
        ) and entry.cnes not in [e.cnes for e in unique_entries]
