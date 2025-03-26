import pytest
from src.repositories.establishment_repository import EstablishmentRepository
from src.interfaces.web_scraper import CNESScraper
from unittest.mock import Mock, patch

@pytest.fixture
def mock_establishment_repo_return_1():
    """Create a mock establishment repository"""
    repo = Mock(spec=EstablishmentRepository)
    repo.check_establishment.return_value = 1
    return repo

@pytest.fixture
def mock_web_scraper_return_true():
    """Create a mock web scraper that can be controlled in tests"""
    class MockCNESScraper(CNESScraper):
        def __init__(self):
            super().__init__()
            self.validate_result = True
        
        def validate_online(self, cnes, establishment_name):
            return self.validate_result
    
    return MockCNESScraper()