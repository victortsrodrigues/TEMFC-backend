import pytest

from unittest.mock import MagicMock, patch
from io import StringIO
from core.services.validation.range_40_validator import Range40Validator
from core.services.validation.range_30_validator import Range30Validator
from core.services.validation.range_20_validator import Range20Validator
from core.services.validation.range_10_validator import Range10Validator
from core.models.validation_result import ProfessionalExperienceValidator
from errors.data_processing_error import DataProcessingError


def test_data_processor_validation_strategies(data_processor):
    """Test that the validation strategies are correctly initialized."""
    assert len(data_processor.VALIDATION_STRATEGIES) == 4
    assert isinstance(data_processor.VALIDATION_STRATEGIES[0], Range40Validator)
    assert isinstance(data_processor.VALIDATION_STRATEGIES[1], Range30Validator)
    assert isinstance(data_processor.VALIDATION_STRATEGIES[2], Range20Validator)
    assert isinstance(data_processor.VALIDATION_STRATEGIES[3], Range10Validator)


def test_is_valid_row_checks_cbo_and_chs(
    establishment_data_valid_cbo_family,
    establishment_data_valid_cbo_clinical,
    establishment_data_valid_cbo_generalist,
    establishment_data_invalid_chs,
    establishment_data_invalid_cbo,
    data_processor,
):
    """Test _is_valid_row method with different CBO descriptions and CHS values."""

    # Test valid scenarios
    assert (
        data_processor._is_valid_row(establishment_data_valid_cbo_family, ["12345"], 10)
        == True
    )

    assert (
        data_processor._is_valid_row(
            establishment_data_valid_cbo_clinical, ["12345"], 10
        )
        == True
    )
    
    assert (
        data_processor._is_valid_row(
            establishment_data_valid_cbo_generalist, ["12345"], 10
        )
        == True
    )

    # Test invalid scenarios
    assert (
        data_processor._is_valid_row(establishment_data_invalid_chs, ["12345"], 10)
        == False
    )

    assert (
        data_processor._is_valid_row(establishment_data_invalid_cbo, ["12345"], 10)
        == False
    )


def test_validate_columns_with_valid_columns(data_processor):
    """Test _validate_columns method with valid column names."""
    fieldnames = [
        "CNES",
        "IBGE",
        "ESTABELECIMENTO",
        "CHS AMB.",
        "DESCRICAO CBO",
        "COMP.",
    ]

    # This should not raise an exception
    data_processor._validate_columns(fieldnames)


def test_validate_columns_with_missing_columns(data_processor):
    """Test _validate_columns method with missing column names."""
    fieldnames = [
        "CNES",
        "IBGE",
        "ESTABELECIMENTO",
        "CHS AMB.",
        "DESCRICAO CBO",
    ]  # Missing "COMP."

    with pytest.raises(DataProcessingError) as excinfo:
        data_processor._validate_columns(fieldnames)

    assert "CSV data format is invalid" in str(excinfo.value)
    assert "COMP." in str(excinfo.value.details.get("missing_columns"))


def test_validate_columns_with_invalid_structure(data_processor):
    """Test _validate_columns method with invalid structure."""
    fieldnames = None  # Invalid structure

    with pytest.raises(DataProcessingError) as excinfo:
        data_processor._validate_columns(fieldnames)

    assert "CSV structure is invalid" in str(excinfo.value)


def test_process_csv_handles_exception(data_processor, tmp_path):
    """Test process_csv method handles exceptions."""
    csv_content = "CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.\n"
    csv_content += "12345;5408102;Hospital A;40;MÉDICO DA FAMÍLIA;01/2023\n"
    csv_file = StringIO(csv_content)
    overall_result = {}
    body = {"name": "test_file"}

    # Simulate an exception in one of the internal methods
    with patch.object(
        data_processor, "_validate_columns", side_effect=Exception("Simulated error")
    ), patch.object(data_processor.logger, "error") as mock_logger:

        with pytest.raises(DataProcessingError) as excinfo:
            data_processor.process_csv(csv_file, overall_result, body)

    assert "Failed to process CSV data" in str(excinfo.value)
    assert "test_file" in str(excinfo.value.details.get("input"))
    assert mock_logger.called


def test_process_csv_with_string_content(data_processor):
    """Test processing CSV with string content."""
    csv_content = "CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.\n"
    csv_content += "12345;5408102;Hospital A;40;MÉDICO DA FAMÍLIA;202301\n"

    overall_result = {}
    body = {"name": "in-memory-data"}

    with patch(
        "utils.cbo_checker.CBOChecker.contains_familia_terms", return_value=True
    ), patch.object(
        data_processor.establishment_validator,
        "check_establishment",
        return_value=["12345"],
    ), patch(
        "utils.date_parser.DateParser.format_yyyymm_to_mm_yyyy", return_value="01/2023"
    ):
        result = data_processor.process_csv(csv_content, overall_result, body)

    assert result > 0
    assert "in-memory-data" in overall_result


def test_process_validator_calls_post_validate(data_processor):
    """Test _process_validator calls post_validate if available."""
    mock_validator = MagicMock()
    mock_validator.lower_bound = 40
    mock_validator.post_validate = MagicMock()

    mock_result = MagicMock(spec=ProfessionalExperienceValidator)
    mock_result.valid_cnes = ["12345"]

    # Empty CSV reader
    mock_csv_reader = []

    data_processor._process_validator(mock_validator, mock_csv_reader, mock_result)

    # Check that post_validate was called
    mock_validator.post_validate.assert_called_once_with(mock_result)


def test_finalize_processing_sorts_valid_rows(data_processor):
    """Test _finalize_processing sorts valid rows by date."""
    result = ProfessionalExperienceValidator()
    result.valid_rows = [
        {"COMP.": "202303"},
        {"COMP.": "202301"},
        {"COMP.": "202302"},
    ]

    overall_result = {}
    body = {"name": "test_file"}

    with patch(
        "utils.date_parser.DateParser.format_yyyymm_to_mm_yyyy",
        side_effect=["03/2023", "01/2023", "02/2023"],
    ):
        data_processor._finalize_processing(StringIO(), result, overall_result, body)

    # Check that rows are sorted in reverse order
    assert result.valid_rows[0]["COMP."] == "202303"
    assert result.valid_rows[1]["COMP."] == "202302"
    assert result.valid_rows[2]["COMP."] == "202301"


def test_finalize_processing_with_ineligible_candidate(data_processor):
    """Test _finalize_processing with insufficient months to be eligible."""
    result = ProfessionalExperienceValidator()
    result.valid_rows = [{"COMP.": "202301"}, {"COMP.": "202302"}, {"COMP.": "202303"}, {"COMP.": "202304"}]
    result.unique_rows_above_40 = set(["01/2023"])
    result.count_rows_between_30_40 = {"02/2023": 1, "04/2023": 1}
    result.count_rows_between_20_30 = {"03/2023": 1}
    
    overall_result = {}
    body = {"name": "test_file"}
    
    with patch("utils.date_parser.DateParser.format_yyyymm_to_mm_yyyy", side_effect=["01/2023", "02/2023", "03/2023", "04/2023"]):
        data_processor._finalize_processing(StringIO(), result, overall_result, body)
    
    assert overall_result["test_file"]["status"] == "Not eligible"
    assert overall_result["test_file"]["pending"] == 45


def test_process_csv_with_valid_data(data_processor, mock_establishment_validator):
    """Test processing CSV with valid data using StringIO."""
    test_rows = [
        ["12345", "5408102", "Hospital A", "40", "MEDICO DA FAMILIA", "202301"],
        ["12345", "5408102", "Hospital A", "40", "MEDICO DA FAMILIA", "202302"],
    ]
    csv_content = "CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.\n"
    csv_content += "\n".join(";".join(map(str, row)) for row in test_rows)
    csv_file = StringIO(csv_content)

    result = ProfessionalExperienceValidator()
    result.valid_rows = [{"COMP.": "202301"}, {"COMP.": "202302"}]
    result.unique_rows_above_40 = set(["01/2023", "02/2023"])
    
    overall_result = {}
    body = {"name": "in-memory-data"}

    # Also need to patch the establishment validator
    with patch.object(
        data_processor.establishment_validator, 
        "check_establishment", 
        return_value=["12345"]
    ), patch(
        "utils.cbo_checker.CBOChecker.contains_familia_terms", 
        return_value=True
    ):
        # Call the method with all required parameters
        result = data_processor.process_csv(csv_file, overall_result, body)

    # Assert the expected results
    assert result == 2
    assert "in-memory-data" in overall_result
    assert overall_result["in-memory-data"]["status"] == "Not eligible"
    assert overall_result["in-memory-data"]["pending"] == 46


def test_process_validator_handles_invalid_rows(data_processor):
    """Test is _process_validator handles invalid rows correctly."""
    mock_validator = MagicMock(spec=Range40Validator)
    mock_validator.lower_bound = 40
    mock_result = MagicMock(spec=ProfessionalExperienceValidator)
    mock_result.valid_cnes = ["12345"]
    mock_csv_reader = [
        {
            "CNES": "12345",
            "IBGE": "5408102",
            "ESTABELECIMENTO": "Test Clinic",
            "CHS AMB.": "40",
            "DESCRICAO CBO": "MEDICO DA FAMILIA",
            "COMP.": "202301",
        },
        {
            "CNES": "INVALID",
            "IBGE": "INVALID",
            "ESTABELECIMENTO": "Invalid Clinic",
            "CHS AMB.": "NOT A NUMBER",  # Invalid (raise ValueError)
            "DESCRICAO CBO": "INVALID",
            "COMP.": "INVALID_DATE",
        },
    ]

    with patch.object(data_processor.logger, "warning") as mock_logger, patch(
        "utils.date_parser.DateParser.format_yyyymm_to_mm_yyyy", return_value="01/2023"
    ):
        data_processor._process_validator(mock_validator, mock_csv_reader, mock_result)

    mock_validator.validate.assert_called_once()
    mock_logger.assert_called_once()
    assert "Skipping invalid row" in mock_logger.call_args[0][0]
