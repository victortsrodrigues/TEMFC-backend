import pytest
import csv
from io import StringIO
from src.core.services.establishment_validator import EstablishmentValidator


class TestEstablishmentValidator:

    @pytest.fixture
    def csv_reader(self):
        csv_data = StringIO(
            """CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.
test_1;123;Test Hospital;40;MEDICO CLINICO;01/2024
test_2;123;Test Hospital;40;MEDICO CLINICO;01/2024
        """
        )
        return csv.DictReader(csv_data, delimiter=";")

    def test_establishment_validator_valid_entries_db(
        self,
        mock_establishment_repo_return_true,
        mock_web_scraper_return_true,
        csv_reader,
    ):
        """Test that valid entries are correctly identified"""

        validator = EstablishmentValidator(
            mock_establishment_repo_return_true, mock_web_scraper_return_true
        )
        valid_cnes = validator.check_establishment(csv_reader)

        assert len(valid_cnes) == 2
        assert "test_1" in valid_cnes
        assert "test_2" in valid_cnes

    def test_establishment_validator_invalid_entries(
        self,
        mock_establishment_repo_return_false,
        mock_web_scraper_return_true,
        csv_reader,
    ):
        """Test that invalid entries are correctly identified"""

        validator = EstablishmentValidator(
            mock_establishment_repo_return_false, mock_web_scraper_return_true
        )
        valid_cnes = validator.check_establishment(csv_reader)

        assert len(valid_cnes) == 0
        assert "test_1" not in valid_cnes

    def test_establishment_validator_low_hours_entries(
        self, mock_establishment_repo_return_true, mock_web_scraper_return_true
    ):
        """Test that entries with low working hours are filtered out"""

        csv_data = StringIO(
            """CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.
test_low_hours_1;123;Test Hospital;5;MEDICO CLINICO;01/2024
test_low_hours_2;123;Test Hospital;9;MEDICO CLINICO;01/2024
        """
        )
        csv_reader = csv.DictReader(csv_data, delimiter=";")

        validator = EstablishmentValidator(
            mock_establishment_repo_return_true, mock_web_scraper_return_true
        )
        valid_cnes = validator.check_establishment(csv_reader)

        assert len(valid_cnes) == 0

    def test_establishment_validator_non_medical_roles(
        self, mock_establishment_repo_return_true, mock_web_scraper_return_true
    ):
        """Test that non-medical roles are filtered out"""

        csv_data = StringIO(
            """CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.
test_non_medical_1;123;Test Hospital;40;ENFERMEIRO;01/2024
test_non_medical_2;123;Test Hospital;40;MEDICO DE FAMILIA;01/2024
        """
        )
        csv_reader = csv.DictReader(csv_data, delimiter=";")

        validator = EstablishmentValidator(
            mock_establishment_repo_return_true, mock_web_scraper_return_true
        )
        valid_cnes = validator.check_establishment(csv_reader)

        assert len(valid_cnes) == 0

    def test_establishment_validator_duplicate_entries(
        self, mock_establishment_repo_return_true, mock_web_scraper_return_true
    ):
        """Test that duplicate entries are filtered out"""

        csv_data = StringIO(
            """CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.
test_duplicate;123;Test Hospital;40;MEDICO CLINICO;01/2024
test_duplicate;123;Test Hospital;40;MEDICO CLINICO;01/2024
        """
        )
        csv_reader = csv.DictReader(csv_data, delimiter=";")

        validator = EstablishmentValidator(
            mock_establishment_repo_return_true, mock_web_scraper_return_true
        )
        valid_cnes = validator.check_establishment(csv_reader)

        assert len(valid_cnes) == 1
        assert "test_duplicate" in valid_cnes

    def test_establishment_validator_database_error(
        self,
        mock_establishment_repo_database_error,
        mock_web_scraper_return_true,
        csv_reader,
    ):
        """Test handling of database errors"""

        validator = EstablishmentValidator(
            mock_establishment_repo_database_error, mock_web_scraper_return_true
        )
        valid_cnes = validator.check_establishment(csv_reader)

        assert len(valid_cnes) == 0

    def test_establishment_validator_web_scraping_fallback_true(
        self,
        mock_establishment_repo_return_none,
        mock_web_scraper_return_true,
        csv_reader,
    ):
        """Test fallback to web scraping when database validation fails"""

        validator = EstablishmentValidator(
            mock_establishment_repo_return_none, mock_web_scraper_return_true
        )
        valid_cnes = validator.check_establishment(csv_reader)

        assert len(valid_cnes) == 2
        assert "test_1" in valid_cnes

    def test_establishment_validator_web_scraping_faallback_false(
        self,
        mock_establishment_repo_return_false,
        mock_web_scraper_return_false,
        csv_reader,
    ):
        """Test behavior when web scraping fails"""

        validator = EstablishmentValidator(
            mock_establishment_repo_return_false, mock_web_scraper_return_false
        )
        valid_cnes = validator.check_establishment(csv_reader)

        assert len(valid_cnes) == 0
        assert "test_1" not in valid_cnes

    def test_establishment_validator_web_scraping_fallback_error(
        self, mock_establishment_repo_return_none, mock_web_scraper_return_error, csv_reader
    ):
        """Test handling of web scraping errors"""

        validator = EstablishmentValidator(
            mock_establishment_repo_return_none, mock_web_scraper_return_error
        )
        valid_cnes = validator.check_establishment(csv_reader)

        assert len(valid_cnes) == 0
