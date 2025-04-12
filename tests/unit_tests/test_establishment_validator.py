import pytest
import csv
import math

from io import StringIO
from unittest.mock import MagicMock, patch, Mock
from src.core.services.establishment_validator import EstablishmentValidator
from src.core.models.row_process_data import RowProcessData


class TestEstablishmentValidator:

    @pytest.fixture
    def csv_reader(self):
        csv_data = StringIO(
            """CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.
test_1;123;Test Hospital;40;MEDICO CLINICO;202401
test_2;123;Test Hospital;40;MEDICO CLINICO;202401
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
        with patch(
            "utils.date_parser.DateParser.format_yyyymm_to_mm_yyyy",
            return_value="01/2024",
        ):
            valid_cnes = validator.check_establishment(csv_reader)

        assert len(valid_cnes) == 2
        assert "0test_1" in valid_cnes
        assert "0test_2" in valid_cnes


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
        with patch(
            "utils.date_parser.DateParser.format_yyyymm_to_mm_yyyy",
            return_value="01/2024",
        ):
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
test_duplicate;123;Test Hospital;40;MEDICO CLINICO;202401
test_duplicate;123;Test Hospital;40;MEDICO CLINICO;202401
        """
        )
        csv_reader = csv.DictReader(csv_data, delimiter=";")

        validator = EstablishmentValidator(
            mock_establishment_repo_return_true, mock_web_scraper_return_true
        )
        with patch(
            "utils.date_parser.DateParser.format_yyyymm_to_mm_yyyy",
            return_value="01/2024",
        ):
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
        assert "0test_1" in valid_cnes
        assert "0test_2" in valid_cnes


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
        assert "0test_1" not in valid_cnes
        assert "0test_2" not in valid_cnes


    def test_establishment_validator_web_scraping_fallback_error(
        self,
        mock_establishment_repo_return_none,
        mock_web_scraper_return_error,
        csv_reader,
    ):
        """Test handling of web scraping errors"""

        validator = EstablishmentValidator(
            mock_establishment_repo_return_none, mock_web_scraper_return_error
        )
        valid_cnes = validator.check_establishment(csv_reader)

        assert len(valid_cnes) == 0


    def test_create_entry_with_valid_data(self):
        """Test _create_entry method with valid data"""
        validator = EstablishmentValidator(None, None)

        line = {
            "CNES": "123456",
            "IBGE": "7890",
            "ESTABELECIMENTO": "Test Hospital",
            "CHS AMB.": "40.5",
            "DESCRICAO CBO": "MEDICO CLINICO",
            "COMP.": "202301",
        }

        entry = validator._create_entry(line)

        assert entry.cnes == "0123456"  # Should be padded to 7 digits
        assert entry.ibge == "7890"
        assert entry.name == "Test Hospital"
        assert math.isclose(entry.chs_amb, 40.5)
        assert entry.cbo_desc == "MEDICO CLINICO"
        assert entry.comp_value == "01/2023"  # Should be reformatted


    def test_create_entry_with_missing_field(self):
        """Test _create_entry method with missing required field"""
        validator = EstablishmentValidator(None, None)

        line = {
            "CNES": "123456",
            "IBGE": "7890",
            # Missing ESTABELECIMENTO
            "CHS AMB.": "40.5",
            "DESCRICAO CBO": "MEDICO CLINICO",
            "COMP.": "202301",
        }

        with pytest.raises(KeyError) as excinfo:
            validator._create_entry(line)

        assert "ESTABELECIMENTO" in str(excinfo.value)


    def test_create_entry_with_invalid_value(self):
        """Test _create_entry method with invalid value format"""
        validator = EstablishmentValidator(None, None)

        line = {
            "CNES": "123456",
            "IBGE": "7890",
            "ESTABELECIMENTO": "Test Hospital",
            "CHS AMB.": "not_a_number",  # Invalid float
            "DESCRICAO CBO": "MEDICO CLINICO",
            "COMP.": "202301",
        }

        with pytest.raises(ValueError) as excinfo:
            validator._create_entry(line)

        assert "Formato de campo inválido" in str(excinfo.value)


    def test_create_entry_with_invalid_date_format(self):
        """Test _create_entry method with invalid date format"""
        validator = EstablishmentValidator(None, None)

        line = {
            "CNES": "123456",
            "IBGE": "7890",
            "ESTABELECIMENTO": "Test Hospital",
            "CHS AMB.": "40.5",
            "DESCRICAO CBO": "MEDICO CLINICO",
            "COMP.": "2023",  # Invalid date format (should be 6 digits)
        }

        with pytest.raises(ValueError) as excinfo:
            validator._create_entry(line)

        assert "Formato de campo inválido" in str(excinfo.value)


    def test_should_validate_with_clinico_terms(self):
        """Test _should_validate method with valid clinico CBO description"""
        validator = EstablishmentValidator(None, None)

        entry = RowProcessData(
            cnes="1234567",
            ibge="7890",
            name="Test Hospital",
            chs_amb=40.5,
            cbo_desc="MEDICO CLINICO",
            comp_value="01/2023",
        )

        result = validator._should_validate(entry, [])

        assert result is True


    def test_should_validate_with_generalista_terms(self):
        """Test _should_validate method with valid generalista CBO description"""
        validator = EstablishmentValidator(None, None)

        entry = RowProcessData(
            cnes="1234567",
            ibge="7890",
            name="Test Hospital",
            chs_amb=40.5,
            cbo_desc="MEDICO GENERALISTA",
            comp_value="01/2023",
        )

        result = validator._should_validate(entry, [])

        assert result is True


    def test_get_unique_entries_with_invalid_line(self):
        """Test _get_unique_entries method with invalid line that should be skipped"""
        validator = EstablishmentValidator(None, None)

        csv_data = StringIO(
            """CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.
valid;123;Test Hospital;40;MEDICO CLINICO;202401
invalid;;Test Hospital;invalid_chs;MEDICO CLINICO;202401
        """
        )
        csv_reader = csv.DictReader(csv_data, delimiter=";")

        unique_entries = validator._get_unique_entries(csv_reader)

        assert len(unique_entries) == 1
        assert unique_entries[0].cnes == "00valid"


    def test_empty_csv_data(
        self, mock_establishment_repo_return_true, mock_web_scraper_return_true
    ):
        """Test behavior with empty CSV data"""
        validator = EstablishmentValidator(
            mock_establishment_repo_return_true, mock_web_scraper_return_true
        )

        csv_data = StringIO(
            """CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.
        """
        )
        csv_reader = csv.DictReader(csv_data, delimiter=";")

        valid_cnes = validator.check_establishment(csv_reader)

        assert len(valid_cnes) == 0


