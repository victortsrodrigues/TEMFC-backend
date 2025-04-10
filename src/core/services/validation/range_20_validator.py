from .base_validator import BaseValidator
from core.models.validation_result import ProfessionalExperienceValidator
from core.models.row_process_data import RowProcessData

class Range20Validator(BaseValidator):
    """Validator for rows with values in the range [20, 30)."""

    MAX_OCCURENCY_20 = 2

    def __init__(self):
        super().__init__(20, 30)

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

        occurrency_comp_with_value_20_30 = result.count_rows_between_20_30.get(row_process_data.comp_value, 0)
        if occurrency_comp_with_value_20_30 < self.MAX_OCCURENCY_20:
            result.count_rows_between_20_30[row_process_data.comp_value] = occurrency_comp_with_value_20_30 + 1
            result.valid_rows.append(row)

    def post_validate(self, result: ProfessionalExperienceValidator) -> None:
        """
        Perform post-validation processing for range 20.

        Args:
            result (ProfessionalExperienceValidator): Validation result object.
        """
        self._promote_overlapping_values_20_30(result)

    def _promote_overlapping_values_20_30(self, result: ProfessionalExperienceValidator) -> None:
        """Promote overlapping values between ranges [20, 30) and [30, 40)."""
        common = set(result.count_rows_between_30_40.keys()) & set(result.count_rows_between_20_30.keys())
        for comp_value in common:
            del result.count_rows_between_30_40[comp_value]
            del result.count_rows_between_20_30[comp_value]
            result.unique_rows_above_40.add(comp_value)