import pytest
import csv
from io import StringIO
from src.core.services.establishment_validator import EstablishmentValidator


def test_establishment_validator_valid_entries_db(
    mock_establishment_repo_return_true, mock_web_scraper_return_true
):
    # Setup test CSV data
    csv_data = StringIO(
        """CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.
test_valid_1;123;Test Hospital;40;MEDICO CLINICO;01/2024
test_valid_2;123;Test Hospital;40;MEDICO CLINICO;01/2024
    """
    )
    csv_reader = csv.DictReader(csv_data, delimiter=";")

    validator = EstablishmentValidator(
        mock_establishment_repo_return_true, mock_web_scraper_return_true
    )
    valid_cnes = validator.check_establishment(csv_reader)

    assert len(valid_cnes) == 2
    assert "test_valid_1" in valid_cnes
    assert "test_valid_2" in valid_cnes

def test_establishment_validator_invalid_entries(
    mock_establishment_repo_return_false, mock_web_scraper_return_true
):
    # Setup test CSV data
    csv_data = StringIO(
        """CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.
    test_valid_159_152;123;Test Hospital;40;MEDICO CLINICO;01/2024
    """
    )
    csv_reader = csv.DictReader(csv_data, delimiter=";")

    validator = EstablishmentValidator(
        mock_establishment_repo_return_false, mock_web_scraper_return_true
    )
    valid_cnes = validator.check_establishment(csv_reader)

    assert len(valid_cnes) == 0
    assert "test_valid_159_152" not in valid_cnes