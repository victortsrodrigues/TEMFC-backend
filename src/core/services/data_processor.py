import csv
import logging
from typing import Dict
from core.models.validation_result import ProfessionalExperienceValidator
from core.models.row_process_data import RowProcessData
from core.services.validation.range_40_validator import Range40Validator
from core.services.validation.range_30_validator import Range30Validator
from core.services.validation.range_20_validator import Range20Validator
from core.services.validation.range_10_validator import Range10Validator
from utils.date_parser import DateParser
from utils.cbo_checker import CBOChecker


class DataProcessor:
    VALIDATION_STRATEGIES = [
        Range40Validator(),
        Range30Validator(),
        Range20Validator(),
        Range10Validator(),
    ]

    def __init__(self, establishment_validator):
        self.establishment_validator = establishment_validator
        self.logger = logging.getLogger(__name__)

    def process_csv(self, file_path: str, overall_result: Dict) -> float:
        try:
            result = ProfessionalExperienceValidator()
            result.file_path = file_path

            with open(file_path, "r", encoding="utf-8") as file:
                csv_reader = csv.DictReader(file, delimiter=";")
                result.valid_cnes = self.establishment_validator.check_establishment(
                    csv_reader
                )

                for validator in self.VALIDATION_STRATEGIES:
                    file.seek(0)
                    csv_reader = csv.DictReader(file, delimiter=";")
                    self._process_validator(validator, csv_reader, result)

            self._finalize_processing(file_path, result, overall_result)
            return result.calculate_valid_months()

        except Exception as e:
            self.logger.error(f"Error processing CSV {file_path}: {e}")
            return 0

    def _process_validator(self, validator, csv_reader: csv.DictReader, result: ProfessionalExperienceValidator) -> None:
        for row in csv_reader:
            try:
                establishment = RowProcessData(
                    cnes=row["CNES"],
                    ibge=row["IBGE"],
                    name=row["ESTABELECIMENTO"],
                    chs_amb=float(row["CHS AMB."]),
                    cbo_desc=row["DESCRICAO CBO"],
                    comp_value=row["COMP."],
                )

                if self._is_valid_row(
                    establishment, result.valid_cnes, validator.lower_bound
                ):
                    validator.validate(establishment, result, row)

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
        file_path: str,
        result: ProfessionalExperienceValidator,
        overall_result: Dict,
    ) -> None:
        result.valid_rows.sort(
            key=lambda x: DateParser.parse(x["COMP."]), reverse=True
        )

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=result.valid_rows[0].keys() if result.valid_rows else [],
                delimiter=";",
            )
            writer.writeheader()
            writer.writerows(result.valid_rows)

        overall_result[file_path] = {
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