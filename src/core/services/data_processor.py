import csv
import logging
import io
import time

from typing import Dict
from core.models.validation_result import ProfessionalExperienceValidator
from core.models.row_process_data import RowProcessData
from core.services.validation.range_40_validator import Range40Validator
from core.services.validation.range_30_validator import Range30Validator
from core.services.validation.range_20_validator import Range20Validator
from core.services.validation.range_10_validator import Range10Validator
from utils.date_parser import DateParser
from utils.cbo_checker import CBOChecker
from utils.sse_manager import sse_manager
from errors.data_processing_error import DataProcessingError
from errors.establishment_scraping_error import ScrapingError
from errors.database_error import DatabaseError
from errors.establishment_validator_error import EstablishmentValidationError


class DataProcessor:
    """
    Processes CSV data and validates professional experience using various strategies.
    """

    VALIDATION_STRATEGIES = [
        Range40Validator(),
        Range30Validator(),
        Range20Validator(),
        Range10Validator(),
    ]

    REQUIRED_COLUMNS = {
        "CNES",
        "IBGE",
        "ESTABELECIMENTO",
        "CHS AMB.",
        "DESCRICAO CBO",
        "COMP.",
    }

    def __init__(self, establishment_validator):
        """
        Initialize the DataProcessor with an establishment validator.

        Args:
            establishment_validator: Validator to check establishment validity.
        """
        self.establishment_validator = establishment_validator
        self.logger = logging.getLogger(__name__)

    def process_csv(self, csv_input, overall_result: Dict, body: Dict, request_id=None) -> float:
        """
        Process a CSV file containing professional experience data.

        Args:
            csv_input: The input CSV data as a string or file-like object.
            overall_result (Dict): Dictionary to store overall processing results.
            body (Dict): Request body containing metadata like name and CPF.
            request_id: Optional request ID for tracking progress.

        Returns:
            float: The number of valid months of professional experience.

        Raises:
            DataProcessingError: If an error occurs during processing.
        """
        try:
            result = ProfessionalExperienceValidator()
            result.file_path = "in-memory-data"

            if isinstance(csv_input, str):
                file = io.StringIO(csv_input)  # Treat as in-memory CSV string
            else:
                file = csv_input
                file.seek(0)

            with file:
                csv_reader = csv.DictReader(file, delimiter=";")

                # Validate columns before processing
                self._validate_columns(csv_reader.fieldnames)

                # Step 2: Check establishment validity
                result.valid_cnes = self.establishment_validator.check_establishment(
                    csv_reader, request_id
                )
                # Step 3: Process validations
                if request_id:
                    sse_manager.publish_progress(
                        request_id, 
                        3, 
                        "Calculando tempo de atuação válido", 
                        20, 
                        "in_progress"
                    )
                
                time.sleep(2) # Simulate some processing time
                
                for i, validator in enumerate(self.VALIDATION_STRATEGIES):                    
                    file.seek(0)
                    csv_reader = csv.DictReader(file, delimiter=";")
                    self._process_validator(validator, csv_reader, result)
            
            self._finalize_processing(result, overall_result, body)
            valid_months = result.calculate_valid_months()

            return valid_months
        
        except DatabaseError:
            raise
        except ScrapingError:
            raise
        except EstablishmentValidationError:
            raise
        except DataProcessingError:
            raise
        except Exception as e:
            self.logger.error(f"Error processing CSV: {e}")
            raise DataProcessingError(
                "Erro ao processar o histórico profissional.",
                {"input": str(body["name"]), "error_type": type(e).__name__},
            )

    def _validate_columns(self, fieldnames) -> bool:
        """
        Validate that the CSV contains all required columns.

        Args:
            fieldnames: List of column names in the CSV.

        Returns:
            bool: True if validation passes, otherwise raises an exception.

        Raises:
            DataProcessingError: If required columns are missing or invalid.
        """
        try:
            if not fieldnames or not self.REQUIRED_COLUMNS.issubset(fieldnames):
                missing = self.REQUIRED_COLUMNS - set(fieldnames)
                error_msg = f"CSV file missing required columns: {missing}"
                self.logger.error(error_msg)
                raise DataProcessingError(
                    "Formato de dados inválido",
                    {"reason": error_msg, "missing_columns": list(missing)},
                )
        except TypeError as e:
            error_msg = f"Invalid CSV structure: {e}"
            self.logger.error(error_msg)
            raise DataProcessingError("Formato de dados inválido", {"reason": error_msg})

    def _process_validator(
        self,
        validator,
        csv_reader: csv.DictReader,
        result: ProfessionalExperienceValidator,
    ) -> None:
        """
        Process rows in the CSV using a specific validation strategy.

        Args:
            validator: The validation strategy to apply.
            csv_reader (csv.DictReader): Reader object for the CSV data.
            result (ProfessionalExperienceValidator): Object to store validation results.
        """
        for row in csv_reader:
            try:

                comp_value = DateParser.format_yyyymm_to_mm_yyyy(row["COMP."])

                establishment_data = RowProcessData(
                    cnes=row["CNES"],
                    ibge=row["IBGE"],
                    name=row["ESTABELECIMENTO"],
                    chs_amb=float(row["CHS AMB."]),
                    cbo_desc=row["DESCRICAO CBO"],
                    comp_value=comp_value,
                )

                if self._is_valid_row(
                    establishment_data, result.valid_cnes, validator.lower_bound
                ):
                    validator.validate(establishment_data, result, row)

            except (ValueError, KeyError) as e:
                self.logger.warning(f"Skipping invalid row: {e}")

        # Post-processing hook (called once per validator)
        if hasattr(validator, "post_validate"):
            validator.post_validate(result)

    def _is_valid_row(
        self, establishment: RowProcessData, valid_cnes: list, chs_threshold: int
    ) -> bool:
        """
        Check if a row is valid based on thresholds and CBO terms.

        Args:
            establishment (RowProcessData): Data for the current row.
            valid_cnes (list): List of valid CNES codes.
            chs_threshold (int): Minimum CHS threshold for validation.

        Returns:
            bool: True if the row is valid, False otherwise.
        """
        if establishment.chs_amb < chs_threshold:
            return False

        return any(
            [
                CBOChecker.contains_familia_terms(establishment.cbo_desc),
                CBOChecker.contains_clinico_terms(establishment.cbo_desc)
                and establishment.cnes in valid_cnes,
                CBOChecker.contains_generalista_terms(establishment.cbo_desc)
                and establishment.cnes in valid_cnes,
            ]
        )

    def _finalize_processing(
        self,
        result: ProfessionalExperienceValidator,
        overall_result: Dict,
        body: Dict,
    ) -> None:
        """
        Finalize processing by sorting rows and updating the overall result.

        Args:
            result (ProfessionalExperienceValidator): Validation results.
            overall_result (Dict): Dictionary to store overall processing results.
            body (Dict): Request body containing metadata like name and CPF.
        """
        result.valid_rows.sort(
            key=lambda x: DateParser.format_yyyymm_to_mm_yyyy(x["COMP."]), reverse=True
        )

        overall_result[body["name"]] = {
            "status": (
                "Eligible"
                if (valid := result.calculate_valid_months()) >= 48
                else "Not eligible"
            ),
            "pending": max(0, 48 - valid),
            "semesters_40": len(result.unique_rows_above_40) // 6,
            "semesters_30": sum(result.count_rows_between_30_40.values()) // 6,
            "semesters_20": sum(result.count_rows_between_20_30.values()) // 6,
        }
