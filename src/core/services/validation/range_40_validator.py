from .base_validator import BaseValidator
from core.models.validation_result import ProfessionalExperienceValidator
from core.models.row_process_data import RowProcessData

class Range40Validator(BaseValidator):
    def __init__(self):
        super().__init__(40, float('inf'))

    def validate(self, row_process_data: RowProcessData, result: ProfessionalExperienceValidator, row: dict) -> None:
        if self._is_in_range(row_process_data.chs_amb) and row_process_data.comp_value not in result.unique_rows_above_40:
            result.unique_rows_above_40.add(row_process_data.comp_value)
            result.valid_rows.append(row)