from unittest.mock import MagicMock, patch
from core.models.validation_result import ProfessionalExperienceValidator
from io import StringIO
from core.services.validation.range_40_validator import Range40Validator
from core.services.validation.range_30_validator import Range30Validator
from core.services.validation.range_20_validator import Range20Validator
from core.services.validation.range_10_validator import Range10Validator


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

    # # Test invalid scenarios
    assert (
        data_processor._is_valid_row(establishment_data_invalid_chs, ["12345"], 10)
        == False
    )

    assert (
        data_processor._is_valid_row(establishment_data_invalid_cbo, ["12345"], 10)
        == False
    )


def test_process_csv_handles_exception(data_processor, tmp_path):
    """Test process_csv method handles exceptions."""
    csv_content = "CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.\n"
    csv_content += "12345;5408102;Hospital A;40;MÉDICO DA FAMÍLIA;01/2023\n"
    csv_file = StringIO(csv_content)
    overall_result = {}
    exception_msg = "Simulated error"
    
    with patch(
        "builtins.open",  # Mock open()
        side_effect=Exception(exception_msg),
    ), patch.object(data_processor.logger, "error") as mock_logger:
      result = data_processor.process_csv(str(csv_file), overall_result)
    
    mock_logger.assert_called_once_with(
        f"Error processing CSV {csv_file}: {exception_msg}"
    )
    assert result == 0


def test_process_csv_with_valid_data(data_processor, mock_establishment_validator):
    """Test processing CSV with valid data using StringIO."""
    test_rows = [
        ["12345", "5408102", "Hospital A", "40", "MEDICO DA FAMILIA", "01/2023"],
        ["12345", "5408102", "Hospital A", "40", "MEDICO DA FAMILIA", "02/2023"],
        ["12345", "5408102", "Hospital A", "40", "MEDICO DA FAMILIA", "03/2023"],
    ]
    csv_content = "CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.\n"
    csv_content += "\n".join(";".join(map(str, row)) for row in test_rows)
    csv_file = StringIO(csv_content)

    overall_result = {}

    with patch(
        "core.services.validation.range_40_validator.Range40Validator.validate"
    ) as mock_validate:

        def side_effect(row_process_data, result, row):
            if row_process_data.comp_value not in result.unique_rows_above_40:
                result.unique_rows_above_40.add(row_process_data.comp_value)
                result.valid_rows.append(row)

        mock_validate.side_effect = side_effect

        with patch(
            "utils.cbo_checker.CBOChecker.contains_familia_terms", return_value=True
        ):
            result = data_processor.process_csv(csv_file, overall_result)

    assert result == 3
    assert "in-memory-data" in overall_result
    assert overall_result["in-memory-data"]["status"] == "Not eligible"
    assert overall_result["in-memory-data"]["pending"] == 45
    assert mock_validate.call_count == 3


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
            "COMP.": "01/2023",
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

    with patch.object(data_processor.logger, "warning") as mock_logger:
        data_processor._process_validator(mock_validator, mock_csv_reader, mock_result)

    mock_validator.validate.assert_called_once()
    mock_logger.assert_called_once_with(
        "Skipping invalid row: could not convert string to float: 'NOT A NUMBER'"
    )


