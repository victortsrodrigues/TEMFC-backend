from src.core.models.validation_result import ProfessionalExperienceValidator
import math

def test_calculate_valid_months():
    validator = ProfessionalExperienceValidator()
    validator.unique_rows_above_40 = set([1, 2, 3])
    validator.count_rows_between_30_40 = {1: 1, 2: 1}
    validator.count_rows_between_20_30 = {1: 1, 2: 1}
    validator.count_rows_between_10_20 = {1: 1, 2: 1}

    assert math.isclose(validator.calculate_valid_months(), 5.5)