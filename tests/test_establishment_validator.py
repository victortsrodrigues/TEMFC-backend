import pytest
import csv
from io import StringIO
from src.core.services.establishment_validator import EstablishmentValidator


def test_establishment_validator_valid_entries_db(
    mock_establishment_repo_return_true, mock_web_scraper_return_true
):
    """Test that valid entries are correctly identified"""
    
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
    """Test that invalid entries are correctly identified"""

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
    
    
def test_establishment_validator_low_hours_entries(
    mock_establishment_repo_return_true, mock_web_scraper_return_true
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
    mock_establishment_repo_return_true, mock_web_scraper_return_true
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
    mock_establishment_repo_return_true, mock_web_scraper_return_true
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
    mock_establishment_repo_database_error, mock_web_scraper_return_true
):
    """Test handling of database errors"""
    
    csv_data = StringIO(
        """CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.
test_db_error;123;Test Hospital;40;MEDICO CLINICO;01/2024
    """
    )
    csv_reader = csv.DictReader(csv_data, delimiter=";")

    validator = EstablishmentValidator(mock_establishment_repo_database_error, mock_web_scraper_return_true)
    valid_cnes = validator.check_establishment(csv_reader)

    assert len(valid_cnes) == 0


def test_establishment_validator_web_scraping_fallback_true(
    mock_establishment_repo_return_none, mock_web_scraper_return_true
):
    """Test fallback to web scraping when database validation fails"""
    csv_data = StringIO(
        """CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.
test_scraper_true;123;Test Hospital;40;MEDICO CLINICO;01/2024
    """
    )
    csv_reader = csv.DictReader(csv_data, delimiter=";")

    validator = EstablishmentValidator(
        mock_establishment_repo_return_none, mock_web_scraper_return_true
    )
    valid_cnes = validator.check_establishment(csv_reader)

    assert len(valid_cnes) == 1
    assert "test_scraper_true" in valid_cnes
    

def test_establishment_validator_web_scraping_faallback_false(
    mock_establishment_repo_return_false, mock_web_scraper_return_false
):
    """Test behavior when web scraping fails"""

    csv_data = StringIO(
        """CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.
test_scraper_false;123;Test Hospital;40;MEDICO CLINICO;01/2024
    """
    )
    csv_reader = csv.DictReader(csv_data, delimiter=";")

    validator = EstablishmentValidator(
        mock_establishment_repo_return_false, mock_web_scraper_return_false
    )
    valid_cnes = validator.check_establishment(csv_reader)

    assert len(valid_cnes) == 0
    assert "test_scraper_false" not in valid_cnes    

def test_establishment_validator_web_scraping_fallback_error(
    mock_establishment_repo_return_none, mock_web_scraper_return_error
):
    """Test handling of web scraping errors"""
    
    csv_data = StringIO(
        """CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.
test_scraper_error;123;Test Hospital;40;MEDICO CLINICO;01/2024
    """
    )
    csv_reader = csv.DictReader(csv_data, delimiter=";")
    
    validator = EstablishmentValidator(
        mock_establishment_repo_return_none, mock_web_scraper_return_error
    )
    valid_cnes = validator.check_establishment(csv_reader)
    
    assert len(valid_cnes) == 0