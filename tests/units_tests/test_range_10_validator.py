import pytest
from src.core.services.validation.range_10_validator import Range10Validator
from src.core.models.validation_result import ProfessionalExperienceValidator


class TestRange10Validator:
    def setup_method(self, method):
        self.validator = Range10Validator()
        self.result = ProfessionalExperienceValidator()

    def test_validator_initialization(self):
        """Test that the validator is initialized with the correct CHS bounds."""
        validator = self.validator
        assert validator.lower_bound == 10
        assert validator.upper_bound == 20

    def test_validate_row_below_lower_bound(
        self, create_dinamic_mock_establishment_data
    ):
        """Verify that rows with CHS below 10 are not validated."""
        validator = self.validator
        result = self.result

        row_data = create_dinamic_mock_establishment_data(
            chs_amb=8, comp_value="01/2023"
        )
        mock_row = {}

        validator.validate(row_data, result, mock_row)

        assert len(result.valid_rows) == 0
        assert len(result.count_rows_between_10_20) == 0

    def test_validate_row_in_range_first_occurrences(
        self, create_dinamic_mock_establishment_data
    ):
        """Test validation for rows within 10-20 CHS range for initial occurrences."""
        validator = self.validator
        result = self.result

        row_data = create_dinamic_mock_establishment_data(
            chs_amb=15, comp_value="01/2023"
        )
        mock_row = {"COMP.": "01/2023"}

        validator.validate(row_data, result, mock_row)

        assert result.count_rows_between_10_20.get("01/2023") == 1
        assert mock_row in result.candidate_to_valid_rows_10["01/2023"]

    def test_validate_row_above_max_occurrences(
        self, create_dinamic_mock_establishment_data
    ):
        """Ensure rows are not added beyond MAX_OCCURENCY_10 limit."""
        validator = self.validator
        result = self.result

        comp_value = "01/2023"

        # Fill up to max occurrences
        for _ in range(validator.MAX_OCCURENCY_10):
            row_data = create_dinamic_mock_establishment_data(
                chs_amb=10, comp_value=comp_value
            )
            mock_row = {"COMP.": comp_value}
            validator.validate(row_data, result, mock_row)

        # Try to add one more row
        row_data = create_dinamic_mock_establishment_data(
            chs_amb=10, comp_value=comp_value
        )
        mock_row = {"COMP.": comp_value}
        validator.validate(row_data, result, mock_row)

        assert result.count_rows_between_10_20.get(comp_value) == 4
        assert len(result.added_to_valid_rows_10[comp_value]) == 4

    def test_validate_row_already_in_unique_rows_above_40(
        self, create_dinamic_mock_establishment_data
    ):
        """Test that rows are not validated if already in unique_rows_above_40."""
        validator = self.validator
        result = self.result

        comp_value = "01/2023"
        result.unique_rows_above_40.add(comp_value)

        row_data = create_dinamic_mock_establishment_data(
            chs_amb=10, comp_value=comp_value
        )
        mock_row = {"COMP.": comp_value}

        validator.validate(row_data, result, mock_row)

        assert len(result.count_rows_between_10_20) == 0
        assert len(result.candidate_to_valid_rows_10) == 0

    
    def test_validate_promotion_to_40(self, create_dinamic_mock_establishment_data):
        """
        Test promotion of rows to 40 CHS range.

        Verifies:
        - Rows are promoted to 40 CHS range when they meet the criteria.
        - Rows are not promoted if they do not meet the criteria.
        """
        validator = self.validator
        result = self.result

        comp_value = "01/2023"
        
        # Add one row of 30
        self.result.count_rows_between_30_40[comp_value] = 1
        
        # Add one row of 10
        row_data = create_dinamic_mock_establishment_data(
            chs_amb=10, comp_value=comp_value
        )
        mock_row = {"COMP.": comp_value}
        validator.validate(row_data, result, mock_row)
        
        assert comp_value in result.unique_rows_above_40
        assert comp_value not in result.count_rows_between_30_40
    

    def test_validate_promotion_to_30(self, create_dinamic_mock_establishment_data):
        """
        Test promotion of rows to 30 CHS range."""
        validator = self.validator
        result = self.result
        
        comp_value = "01/2023"
        
        self.result.count_rows_between_30_40[comp_value] = 0
        
        # Add one row of 20
        self.result.count_rows_between_20_30[comp_value] = 1
        
        # Add one row of 10
        row_data = create_dinamic_mock_establishment_data(
            chs_amb=10, comp_value=comp_value
        )
        mock_row = {"COMP.": comp_value}
        validator.validate(row_data, result, mock_row)
        
        assert comp_value in result.count_rows_between_30_40
        assert comp_value not in result.count_rows_between_20_30
      
      
    @pytest.mark.parametrize(
        "row_count, expected_destination",
        [
            (4, "unique_rows_above_40"),
            (3, "count_rows_between_30_40"),
            (2, "count_rows_between_20_30"),
        ],
    )
    def test_post_validate_promotions(
        self, row_count, expected_destination, create_dinamic_mock_establishment_data
    ):
        """
        Parameterized test for different post-validation promotion scenarios.
        Tests promotions to:
        - 40 CHS range (4 rows)
        - 30 CHS range (3 rows)
        - 20 CHS range (2 rows)
        """
        validator = self.validator
        result = self.result

        comp_value = "01/2023"

        # Simulate rows for a specific comp_value
        for _ in range(row_count):
            row_data = create_dinamic_mock_establishment_data(
                chs_amb=10, comp_value=comp_value
            )
            mock_row = {"COMP.": comp_value}
            validator.validate(row_data, result, mock_row)

        validator.post_validate(result)

        if expected_destination == "unique_rows_above_40":
            assert comp_value in result.unique_rows_above_40
        elif expected_destination == "count_rows_between_30_40":
            assert comp_value in result.count_rows_between_30_40
        else:
            assert comp_value in result.count_rows_between_20_30
            

