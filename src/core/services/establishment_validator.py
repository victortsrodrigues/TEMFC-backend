from repositories.establishment_repository import EstablishmentRepository
from utils.cbo_checker import CBOChecker
from interfaces.web_scraper import CNESScraper
from core.models.row_process_data import RowProcessData
from utils.date_parser import DateParser
from errors.establishment_validator_error import EstablishmentValidationError
import logging

class EstablishmentValidator:
    def __init__(self, repo, scraper):
        self.repo = repo
        self.scraper = scraper
        self.logger = logging.getLogger(__name__)

    def check_establishment(self, csv_reader):
        try:
            unique_entries = self._get_unique_entries(csv_reader)
            if not unique_entries:
                    self.logger.warning("No valid unique entries found in CSV data")
            valid_cnes = self._get_valid_cnes(unique_entries)
            return valid_cnes
        except Exception as e:
            self.logger.error(f"Error in check_establishment: {str(e)}")
            raise EstablishmentValidationError(
                "Failed to validate establishments",
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
                "Failed to process CSV entries",
                {"reason": str(e)}
            )

    def _get_valid_cnes(self, unique_entries):
        valid_cnes = []
        for entry in unique_entries:
            if entry.cnes not in valid_cnes:
                try:
                    cnes_validation = self.repo.check_establishment(entry.ibge + entry.cnes)
                    if cnes_validation is True:
                        valid_cnes.append(entry.cnes)
                    elif cnes_validation is None:
                        online_validation_success = self.scraper.validate_online(entry.cnes, entry.name)
                        if online_validation_success:
                            valid_cnes.append(entry.cnes)
                except Exception as e:
                    self.logger.error(f"Failed to validate CNES {entry.cnes}: {e}")
                    continue
        return valid_cnes

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
            raise KeyError(f"Missing required field: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid value format: {e}")

    def _should_validate(self, entry, unique_entries):
        return entry.chs_amb >= 10 and (
            CBOChecker.contains_clinico_terms(entry.cbo_desc) or 
            CBOChecker.contains_generalista_terms(entry.cbo_desc)
        ) and entry.cnes not in [e.cnes for e in unique_entries]