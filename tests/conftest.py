import pytest
from src.repositories.establishment_repository import EstablishmentRepository
from src.interfaces.web_scraper import CNESScraper
from unittest.mock import Mock, patch

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