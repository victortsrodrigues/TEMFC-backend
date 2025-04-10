from .base_validator import BaseValidator
from core.models.validation_result import ProfessionalExperienceValidator
from core.models.row_process_data import RowProcessData

class Range30Validator(BaseValidator):
    """Validator for rows with values in the range [30, 40)."""

    MAX_OCCURENCY_30 = 2

    def __init__(self):
        super().__init__(30, 40)

    def validate(self, row_process_data: RowProcessData, result: ProfessionalExperienceValidator, row: dict) -> None:
        """
        Validate a row and update the result object.

        Args:
            row_process_data (RowProcessData): Processed row data.
            result (ProfessionalExperienceValidator): Validation result object.
            row (dict): Original row data.
        """
        if not self._is_in_range(row_process_data.chs_amb) or row_process_data.comp_value in result.unique_rows_above_40:
            return
            
        occurrency_comp_with_value_30_40 = result.count_rows_between_30_40.get(row_process_data.comp_value, 0)
        if occurrency_comp_with_value_30_40 < self.MAX_OCCURENCY_30:
            result.count_rows_between_30_40[row_process_data.comp_value] = occurrency_comp_with_value_30_40 + 1
            result.valid_rows.append(row)

    def post_validate(self, result: ProfessionalExperienceValidator) -> None:
        """
        Perform post-validation processing for range 30.

        Args:
            result (ProfessionalExperienceValidator): Validation result object.
        """
        self._handle_promotion_to_40(result)

    def _handle_promotion_to_40(self, result: ProfessionalExperienceValidator) -> None:
        for comp_value, count in list(result.count_rows_between_30_40.items()):
            if count >= self.MAX_OCCURENCY_30:
                result.unique_rows_above_40.add(comp_value)
                del result.count_rows_between_30_40[comp_value]