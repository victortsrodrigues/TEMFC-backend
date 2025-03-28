from abc import ABC, abstractmethod
from core.models.validation_result import ProfessionalExperienceValidator
from core.models.row_process_data import RowProcessData

class BaseValidator(ABC):
    def __init__(self, lower_bound: int, upper_bound: int):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        
    @abstractmethod
    def validate(self, line: RowProcessData, result: ProfessionalExperienceValidator, row: dict) -> None:
        pass
    
    def post_validate(self, result: ProfessionalExperienceValidator) -> None:
        """Optional method for post-processing after all lines are validated"""
        pass
      
    def _is_in_range(self, chs_amb: float) -> bool:
        return self.lower_bound <= chs_amb < self.upper_bound
