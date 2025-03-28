import pytest
from src.core.services.validation.range_30_validator import Range30Validator
from src.core.models.validation_result import ProfessionalExperienceValidator


class TestRange30Validator:
    def setup_method(self, method):
        self.validator = Range30Validator()
        self.result = ProfessionalExperienceValidator()


    def test_validator_initialization(self):
        """Test that the validator is initialized with the correct CHS bounds."""
        validator = self.validator
        assert validator.lower_bound == 30
        assert validator.upper_bound == 40
        
        
    def test_validate_row_below_lower_bound(
        self, create_dinamic_mock_establishment_data
    ):
        """Verify that rows with CHS below 30 are not validated."""
        validator = self.validator
        result = self.result

        row_data = create_dinamic_mock_establishment_data(
            chs_amb=8, comp_value="01/2023"
        )
        mock_row = {}

        validator.validate(row_data, result, mock_row)

        assert len(result.valid_rows) == 0
        assert len(result.count_rows_between_30_40) == 0
        
        
    def test_validate_row_in_range_first_occurrences(
        self, create_dinamic_mock_establishment_data
    ):
        """Test validation for rows within 30-40 CHS range for initial occurrences."""
        validator = self.validator
        result = self.result

        row_data = create_dinamic_mock_establishment_data(
            chs_amb=30, comp_value="01/2023"
        )
        mock_row = {"COMP.": "01/2023"}

        validator.validate(row_data, result, mock_row)

        assert result.count_rows_between_30_40.get("01/2023") == 1
        assert mock_row in result.valid_rows
        assert len(result.valid_rows) == 1
        
        
    def test_validate_row_above_max_occurrences(
        self, create_dinamic_mock_establishment_data
    ):
        """Ensure rows are not added beyond MAX_OCCURENCY_30 limit."""
        validator = self.validator
        result = self.result

        comp_value = "01/2023"

        # Fill up to max occurrences
        for _ in range(validator.MAX_OCCURENCY_30):
            row_data = create_dinamic_mock_establishment_data(
                chs_amb=30, comp_value=comp_value
            )
            mock_row = {"COMP.": comp_value}
            validator.validate(row_data, result, mock_row)

        # Try to add one more row
        row_data = create_dinamic_mock_establishment_data(
            chs_amb=30, comp_value=comp_value
        )
        mock_row = {"COMP.": comp_value}
        validator.validate(row_data, result, mock_row)

        assert result.count_rows_between_30_40.get(comp_value) == 2
        assert mock_row in result.valid_rows
        assert len(result.valid_rows) == 2
        
        
    def test_validate_row_already_in_unique_rows_above_40(
        self, create_dinamic_mock_establishment_data
    ):
      """Test that rows are not validated if already in unique_rows_above_40."""
      validator = self.validator
      result = self.result

      comp_value = "01/2023"
      result.unique_rows_above_40.add(comp_value)

      row_data = create_dinamic_mock_establishment_data(
          chs_amb=30, comp_value=comp_value
      )
      mock_row = {"COMP.": comp_value}

      validator.validate(row_data, result, mock_row)

      assert len(result.count_rows_between_30_40) == 0
      assert len(result.valid_rows) == 0
        
        
    def test_post_validate_promotion(self):
      """Test promotion of overlapping values to unique_rows_above_40"""
      validator = self.validator
      result = self.result
      
      comp_value = "01/2023"
      
      result.count_rows_between_30_40 = {comp_value: validator.MAX_OCCURENCY_30 + 1}
      
      validator.post_validate(result)
      
      assert comp_value in result.unique_rows_above_40
      assert comp_value not in result.count_rows_between_30_40