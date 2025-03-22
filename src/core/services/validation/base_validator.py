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
      
    def handle_overlapping_values_20_30(self, result: ProfessionalExperienceValidator) -> None:
        for comp_value, count in result.count_rows_between_30_40.items():
            if count == 2:
                result.count_rows_between_30_40[comp_value] = 0
                result.unique_rows_above_40.add(comp_value)
        
        common = set(result.count_rows_between_30_40.keys()) & set(result.count_rows_between_20_30.keys())
        for comp_value in common:
            del result.count_rows_between_30_40[comp_value]
            del result.count_rows_between_20_30[comp_value]
            result.unique_rows_above_40.add(comp_value)