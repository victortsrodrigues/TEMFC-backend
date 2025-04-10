from abc import ABC, abstractmethod
from core.models.validation_result import ProfessionalExperienceValidator
from core.models.row_process_data import RowProcessData

class BaseValidator(ABC):
    """Abstract base class for range validators."""

    def __init__(self, lower_bound: int, upper_bound: int):
        """
        Initialize the validator with range bounds.

        Args:
            lower_bound (int): The lower bound of the range.
            upper_bound (int): The upper bound of the range.
        """
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    @abstractmethod
    def validate(self, line: RowProcessData, result: ProfessionalExperienceValidator, row: dict) -> None:
        """
        Validate a single row of data.

        Args:
            line (RowProcessData): Processed row data.
            result (ProfessionalExperienceValidator): Validation result object.
            row (dict): Original row data.
        """
        pass

    def post_validate(self, result: ProfessionalExperienceValidator) -> None:
        """
        Perform post-validation processing.

        Args:
            result (ProfessionalExperienceValidator): Validation result object.
        """
        pass
      
    def _is_in_range(self, chs_amb: float) -> bool:
        """
        Check if a value is within the validator's range.

        Args:
            chs_amb (float): The value to check.

        Returns:
            bool: True if the value is within range, False otherwise.
        """
        return self.lower_bound <= chs_amb < self.upper_bound
