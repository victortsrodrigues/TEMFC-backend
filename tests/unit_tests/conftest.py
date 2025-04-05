import pytest
from src.repositories.establishment_repository import EstablishmentRepository
from src.core.services.core_service import Services
from src.core.services.establishment_validator import EstablishmentValidator
from src.core.services.data_processor import DataProcessor
from src.core.models.row_process_data import RowProcessData
from src.interfaces.web_scraper import CNESScraper
from unittest.mock import Mock, patch

@pytest.fixture
def mock_establishment_services_return_valid():
    """Create a mock services valid"""
    services = Mock(spec=Services)
    services.run_services.return_value = 50
    return  services


@pytest.fixture
def mock_establishment_repo_return_true():
    """Create a mock establishment repository"""
    repo = Mock(spec=EstablishmentRepository)
    repo.check_establishment.return_value = True
    return repo


@pytest.fixture
def mock_establishment_repo_return_false():
    """Create a mock establishment repository"""
    repo = Mock(spec=EstablishmentRepository)
    repo.check_establishment.return_value = False
    return repo

@pytest.fixture
def mock_establishment_repo_return_none():
    """Create a mock establishment repository"""
    repo = Mock(spec=EstablishmentRepository)
    repo.check_establishment.return_value = None
    return repo


@pytest.fixture
def mock_establishment_repo_database_error():
    """Create a mock establishment repository"""
    repo = Mock(spec=EstablishmentRepository)
    repo.check_establishment.side_effect = Exception("Database error")
    return repo


@pytest.fixture
def mock_web_scraper_return_true():
    """Create a mock CNES web scraper"""
    scraper = Mock(spec=CNESScraper)
    scraper.validate_online.return_value = True
    return scraper


@pytest.fixture
def mock_web_scraper_return_false():
    """Create a mock CNES web scraper"""
    scraper = Mock(spec=CNESScraper)
    scraper.validate_online.return_value = False
    return scraper


@pytest.fixture
def mock_web_scraper_return_error():
    """Create a mock CNES web scraper"""
    scraper = Mock(spec=CNESScraper)
    scraper.validate_online.side_effect = Exception("Web scraping error")
    return scraper


@pytest.fixture
def mock_establishment_validator():
    mock_validator = Mock(spec=EstablishmentValidator)
    mock_validator.check_establishment.return_value = ['12345']
    return mock_validator


@pytest.fixture
def data_processor(mock_establishment_validator):
    return DataProcessor(mock_establishment_validator)


@pytest.fixture
def establishment_data_valid_cbo_family():
    return RowProcessData(
        cnes="12345",
        ibge="123",
        name="Test Unit",
        chs_amb=float("40"),
        cbo_desc="MEDICO DA FAMILIA",
        comp_value="01/2023"
    )
    
@pytest.fixture
def establishment_data_valid_cbo_clinical():
    return RowProcessData(
        cnes="12345",
        ibge="123",
        name="Test Unit",
        chs_amb=float("40"),
        cbo_desc="MEDICO CLINICO",
        comp_value="01/2023"
    )
    

@pytest.fixture
def establishment_data_valid_cbo_generalist():
    return RowProcessData(
        cnes="12345",
        ibge="123",
        name="Test Unit",
        chs_amb=float("40"),
        cbo_desc="MEDICO GENERALISTA",
        comp_value="01/2023"
    )


@pytest.fixture
def establishment_data_invalid_chs():
    return RowProcessData(
        cnes="12345",
        ibge="123",
        name="Test Unit",
        chs_amb=float("5"),
        cbo_desc="MEDICO DA FAMILIA",
        comp_value="01/2023"
    )
    
    
@pytest.fixture
def establishment_data_invalid_cbo():
    return RowProcessData(
        cnes="12345",
        ibge="123",
        name="Test Unit",
        chs_amb=float("40"),
        cbo_desc="ENFERMEIRO DA FAMILIA",
        comp_value="01/2023"
    )
    

@pytest.fixture
def create_dinamic_mock_establishment_data():
    def _factory(chs_amb: float, comp_value: str):
        return RowProcessData(
            cnes="12345",
            ibge="123",
            name="Test Unit",
            chs_amb=chs_amb,
            cbo_desc="MEDICO DA FAMILIA",
            comp_value=comp_value
        )
    return _factory 