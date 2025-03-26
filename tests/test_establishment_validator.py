import pytest
import csv
from io import StringIO
from src.core.services.establishment_validator import EstablishmentValidator


def test_establishment_validator_valid_entries(
    mock_establishment_repo_return_1, mock_web_scraper_return_true
):
    # Setup test CSV data
    csv_data = StringIO(
        """CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.
test_valid_159_152;123;Test Hospital;40;MEDICO CLINICO;01/2024
    """
    )
    csv_reader = csv.DictReader(csv_data, delimiter=";")

    validator = EstablishmentValidator(
        mock_establishment_repo_return_1, mock_web_scraper_return_true
    )
    valid_cnes = validator.check_establishment(csv_reader)

    assert len(valid_cnes) == 1
    assert "test_valid_159_152" in valid_cnes
