import pytest
from src.repositories.establishment_repository import EstablishmentRepository
from src.core.services.establishment_validator import EstablishmentValidator
from src.core.services.data_processor import DataProcessor
from src.core.models.row_process_data import RowProcessData
from interfaces.establishment_scraper import CNESScraper
from unittest.mock import Mock, patch

# tests/conftest.py
def pytest_collection_modifyitems(config, items):
    for item in items:
        if "integration_tests" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "unit_tests" in item.nodeid:
            item.add_marker(pytest.mark.unit)
