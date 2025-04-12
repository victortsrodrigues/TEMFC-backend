from src.core.services.validation.range_40_validator import Range40Validator
from src.core.models.validation_result import ProfessionalExperienceValidator


class TestRange40Validator:
    def setup_method(self, method):
        self.validator = Range40Validator()
        self.result = ProfessionalExperienceValidator()


    def test_validator_initialization(self):
        """Test that the validator is initialized with the correct CHS bounds."""
        validator = self.validator
        assert validator.lower_bound == 40
        assert validator.upper_bound == float('inf')
        
        
    def test_validate_row_below_lower_bound(
        self, create_dinamic_mock_establishment_data
    ):
        """Verify that rows with CHS below 40 are not validated."""
        validator = self.validator
        result = self.result

        row_data = create_dinamic_mock_establishment_data(
            chs_amb=8, comp_value="01/2023"
        )
        mock_row = {}

        validator.validate(row_data, result, mock_row)

        assert len(result.valid_rows) == 0
        assert len(result.unique_rows_above_40) == 0
        
        
    def test_validate_row_in_range_first_occurrences(
        self, create_dinamic_mock_establishment_data
    ):
        """Test validation for rows within 40-inf CHS range for initial occurrences."""
        validator = self.validator
        result = self.result

        row_data = create_dinamic_mock_establishment_data(
            chs_amb=40, comp_value="01/2023"
        )
        mock_row = {"COMP.": "01/2023"}

        validator.validate(row_data, result, mock_row)

        assert len(result.unique_rows_above_40) == 1
        assert "01/2023" in result.unique_rows_above_40
        assert len(result.valid_rows) == 1
        assert result.valid_rows[0] == mock_row
        
        
    def test_validate_row_already_in_unique_rows_above_40(
        self, create_dinamic_mock_establishment_data
    ):
      """Test that rows are not validated if already in unique_rows_above_40."""
      validator = self.validator
      result = self.result

      comp_value = "01/2023"
      result.unique_rows_above_40.add(comp_value)

      row_data = create_dinamic_mock_establishment_data(
          chs_amb=40, comp_value=comp_value
      )
      mock_row = {"COMP.": comp_value}

      validator.validate(row_data, result, mock_row)

      assert len(result.unique_rows_above_40) == 1
      assert len(result.valid_rows) == 0
      
  
    def test_validate_multiple_unique_rows(
          self, create_dinamic_mock_establishment_data
      ):
        """Test that rows are not validated if already in unique_rows_above_40."""
        validator = self.validator
        result = self.result

        rows = [
            (create_dinamic_mock_establishment_data(
                chs_amb=40, comp_value="01/2023"
            ), {"COMP.": "01/2023"}),
            (create_dinamic_mock_establishment_data(
                chs_amb=40, comp_value="02/2023"
            ), {"COMP.": "02/2023"}),
        ]
        
        for row, mock_row in rows:
            validator.validate(row, result, mock_row)
        
        assert len(result.unique_rows_above_40) == 2
        assert "01/2023" in result.unique_rows_above_40
        assert "02/2023" in result.unique_rows_above_40
        assert len(result.valid_rows) == 2