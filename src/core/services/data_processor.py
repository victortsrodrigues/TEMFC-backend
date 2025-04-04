import csv
import logging
import io
from pathlib import Path
from typing import Dict
from core.models.validation_result import ProfessionalExperienceValidator
from core.models.row_process_data import RowProcessData
from core.services.validation.range_40_validator import Range40Validator
from core.services.validation.range_30_validator import Range30Validator
from core.services.validation.range_20_validator import Range20Validator
from core.services.validation.range_10_validator import Range10Validator
from utils.date_parser import DateParser
from utils.cbo_checker import CBOChecker
from errors.data_processing_error import DataProcessingError


class DataProcessor:
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
        self.establishment_validator = establishment_validator
        self.logger = logging.getLogger(__name__)

    def process_csv(self, csv_input, overall_result: Dict, body: Dict) -> float:
        try:
            result = ProfessionalExperienceValidator()
            result.file_path = (
                str(csv_input)
                if isinstance(csv_input, (str, Path))
                else "in-memory-data"
            )

            # Open the file if it's a path, or use the object directly
            if isinstance(csv_input, (str, Path)):
                path = Path(csv_input)
                if path.is_file():
                    file = open(path, "r", encoding="utf-8")
                else:
                    file = io.StringIO(csv_input)  # Treat as in-memory CSV string
            else:
                file = csv_input
                file.seek(0)

            with file:
                csv_reader = csv.DictReader(file, delimiter=";")

                # Validate columns before processing
                self._validate_columns(csv_reader.fieldnames)

                result.valid_cnes = self.establishment_validator.check_establishment(
                    csv_reader
                )

                for validator in self.VALIDATION_STRATEGIES:
                    file.seek(0)
                    csv_reader = csv.DictReader(file, delimiter=";")
                    self._process_validator(validator, csv_reader, result)

            self._finalize_processing(csv_input, result, overall_result, body)
            return result.calculate_valid_months()

        except DataProcessingError:
            # Re-raise DataProcessingError exceptions
            raise
        except Exception as e:
            self.logger.error(f"Error processing CSV {csv_input}: {e}")
            # Convert all other exceptions to DataProcessingError
            raise DataProcessingError(
                f"Failed to process CSV data: {str(e)}",
                {"input": str(csv_input), "error_type": type(e).__name__},
            )

    def _validate_columns(self, fieldnames) -> bool:
        """Validate CSV contains all required columns"""
        try:
            if not fieldnames or not self.REQUIRED_COLUMNS.issubset(fieldnames):
                missing = self.REQUIRED_COLUMNS - set(fieldnames)
                error_msg = f"CSV file missing required columns: {missing}"
                self.logger.error(error_msg)
                raise DataProcessingError(
                    "CSV data format is invalid",
                    {"reason": error_msg, "missing_columns": list(missing)},
                )
        except TypeError as e:
            error_msg = f"Invalid CSV structure: {e}"
            self.logger.error(error_msg)
            raise DataProcessingError("CSV structure is invalid", {"reason": error_msg})

    def _process_validator(
        self,
        validator,
        csv_reader: csv.DictReader,
        result: ProfessionalExperienceValidator,
    ) -> None:
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
        csv_input,
        result: ProfessionalExperienceValidator,
        overall_result: Dict,
        body: Dict,
    ) -> None:
        result.valid_rows.sort(
            key=lambda x: DateParser.format_yyyymm_to_mm_yyyy(x["COMP."]), reverse=True
        )

        if isinstance(csv_input, (str, Path)):
            path = Path(csv_input)
            if path.is_file():
                with open(csv_input, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=(
                            result.valid_rows[0].keys() if result.valid_rows else []
                        ),
                        delimiter=";",
                    )
                    writer.writeheader()
                    writer.writerows(result.valid_rows)

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
