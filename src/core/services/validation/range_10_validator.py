from .base_validator import BaseValidator
from core.models.validation_result import ProfessionalExperienceValidator
from core.models.row_process_data import RowProcessData


class Range10Validator(BaseValidator):
    """Validator for rows with values in the range [10, 20)."""

    MAX_OCCURENCY_10 = 4
    MIN_PROMOTION_OCURRENCIES = 2

    def __init__(self):
        super().__init__(10, 20)

    def validate(
        self,
        row_process_data: RowProcessData,
        result: ProfessionalExperienceValidator,
        row: dict,
    ) -> None:
        """
        Validate a row and update the result object.

        Args:
            row_process_data (RowProcessData): Processed row data.
            result (ProfessionalExperienceValidator): Validation result object.
            row (dict): Original row data.
        """
        if (
            not self._is_in_range(row_process_data.chs_amb)
            or row_process_data.comp_value in result.unique_rows_above_40
        ):
            return

        if self._should_count_row_10_and_append_to_candidates(
            row_process_data.comp_value, result
        ):
            result.count_rows_between_10_20[row_process_data.comp_value] = (
                result.count_rows_between_10_20.get(row_process_data.comp_value, 0) + 1
            )
            
            result.candidate_to_valid_rows_10[row_process_data.comp_value].append(row)

            self._process_candidate_rows(row_process_data.comp_value, result)

        elif self._should_upgrade_to_40(row_process_data.comp_value, result):
            del result.count_rows_between_30_40[row_process_data.comp_value]
            result.unique_rows_above_40.add(row_process_data.comp_value)
            result.valid_rows.append(row)

        elif self._should_upgrade_to_30(row_process_data.comp_value, result):
            del result.count_rows_between_20_30[row_process_data.comp_value]
            if result.count_rows_between_30_40.get(row_process_data.comp_value, 0) == 0:
                result.count_rows_between_30_40[row_process_data.comp_value] = 1
                result.valid_rows.append(row)

    def _should_count_row_10_and_append_to_candidates(
        self, comp_value: str, result: ProfessionalExperienceValidator
    ) -> bool:
        """
        Check if a row should be counted and appended to candidates.

        Args:
            comp_value (str): The value to check.
            result (ProfessionalExperienceValidator): Validation result object.

        Returns:
            bool: True if the row should be counted and appended, False otherwise.
        """
        return (
            result.count_rows_between_30_40.get(comp_value, 0) == 0
            and result.count_rows_between_20_30.get(comp_value, 0) == 0
            and result.count_rows_between_10_20.get(comp_value, 0)
            < self.MAX_OCCURENCY_10
        )

    def _process_candidate_rows(
        self, comp_value: str, result: ProfessionalExperienceValidator
    ) -> None:
        """
        Process candidate rows for validation.

        Args:
            comp_value (str): The value to process.
            result (ProfessionalExperienceValidator): Validation result object.
        """
        if self._has_min_ocurrencies_to_promotion(comp_value, result):
            self._validate_row_save_history_and_clear_candidates(comp_value, result)

        else:
            self._add_to_valid_if_has_previous_added_rows(comp_value, result)

    def _has_min_ocurrencies_to_promotion(
        self, comp_value: str, result: ProfessionalExperienceValidator
    ) -> bool:
        """
        Check if a candidate has the minimum occurrences for promotion.

        Args:
            comp_value (str): The value to check.
            result (ProfessionalExperienceValidator): Validation result object.

        Returns:
            bool: True if the candidate has the minimum occurrences, False otherwise.
        """
        return (
            len(result.candidate_to_valid_rows_10[comp_value])
            >= self.MIN_PROMOTION_OCURRENCIES
        )

    def _validate_row_save_history_and_clear_candidates(
        self, comp_value: str, result: ProfessionalExperienceValidator
    ) -> None:
        """
        Validate rows, save history, and clear candidate rows.

        Args:
            comp_value (str): The value to process.
            result (ProfessionalExperienceValidator): Validation result object.
        """
        for row in result.candidate_to_valid_rows_10[comp_value]:
            result.valid_rows.append(row)
        self._update_added_rows_and_clear_candidate_rows(comp_value, result)

    def _update_added_rows_and_clear_candidate_rows(
        self, comp_value: str, result: ProfessionalExperienceValidator
    ) -> None:
        """
        Update added rows and clear candidate rows.

        Args:
            comp_value (str): The value to process.
            result (ProfessionalExperienceValidator): Validation result object.
        """
        result.added_to_valid_rows_10[comp_value].extend(
            result.candidate_to_valid_rows_10[comp_value]
        )
        result.candidate_to_valid_rows_10[comp_value].clear()

    def _add_to_valid_if_has_previous_added_rows(
        self, comp_value: str, result: ProfessionalExperienceValidator
    ) -> None:
        """
        Add to valid rows if there are previously added rows.

        Args:
            comp_value (str): The value to process.
            result (ProfessionalExperienceValidator): Validation result object.
        """
        if comp_value in result.added_to_valid_rows_10:
            result.valid_rows.append(result.candidate_to_valid_rows_10[comp_value][0])
            self._update_added_rows_and_clear_candidate_rows(comp_value, result)

    def _should_upgrade_to_40(
        self, comp_value: str, result: ProfessionalExperienceValidator
    ) -> bool:
        """
        Check if a candidate should be upgraded to range 40.

        Args:
            comp_value (str): The value to check.
            result (ProfessionalExperienceValidator): Validation result object.

        Returns:
            bool: True if the candidate should be upgraded, False otherwise.
        """
        return (
            comp_value in result.count_rows_between_30_40
            and result.count_rows_between_30_40[comp_value] == 1
        )

    def _should_upgrade_to_30(
        self, comp_value: str, result: ProfessionalExperienceValidator
    ) -> bool:
        """
        Check if a candidate should be upgraded to range 30.

        Args:
            comp_value (str): The value to check.
            result (ProfessionalExperienceValidator): Validation result object.

        Returns:
            bool: True if the candidate should be upgraded, False otherwise.
        """
        return (
            comp_value in result.count_rows_between_20_30
            and result.count_rows_between_20_30[comp_value] == 1
        )

    def post_validate(self, result: ProfessionalExperienceValidator) -> None:
        """
        Perform post-validation processing for range 10.

        Args:
            result (ProfessionalExperienceValidator): Validation result object.
        """
        self._handle_promotions(result)

    def _handle_promotions(self, result: ProfessionalExperienceValidator) -> None:
        """
        Handle promotions for candidates based on their counts.

        Args:
            result (ProfessionalExperienceValidator): Validation result object.
        """
        for comp_value, count in list(result.count_rows_between_10_20.items()):
            if count >= 4:
                result.unique_rows_above_40.add(comp_value)
            elif count >= 3:
                result.count_rows_between_30_40[comp_value] = 1
            elif count >= 2:
                result.count_rows_between_20_30[comp_value] = 1
