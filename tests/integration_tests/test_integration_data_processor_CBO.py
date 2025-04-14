import pytest

from src.core.services.data_processor import DataProcessor
from src.core.services.establishment_validator import EstablishmentValidator
from src.repositories.establishment_repository import EstablishmentRepository
from src.interfaces.establishment_scraper import CNESScraper


class TestDataProcessorCBOIntegration:
    @pytest.fixture
    def data_processor(self):
        """Create an actual data processor with real dependencies"""
        repo = EstablishmentRepository()
        scraper = CNESScraper()
        establishment_validator = EstablishmentValidator(repo, scraper)
        return DataProcessor(establishment_validator)

    def test_process_csv_valid_family(self, data_processor, csv_factory_chs_cbo):
        """Integration test to verify CSV processing with valid medical professional data"""
        csv_file = csv_factory_chs_cbo()
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert valid_months == 2
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert overall_result["in-memory-data"]["pending"] == 46

    def test_process_csv_invalid_cbo(self, data_processor, csv_factory_chs_cbo):
        custom_data = ["6990193", "350750", "USF COHAB IV BOTUCATU", "40", "ENFERMEIRO", "202303"]

        csv_file = csv_factory_chs_cbo(data=custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert valid_months == 2
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert overall_result["in-memory-data"]["pending"] == 46

    def test_process_csv_valid_clinical(self, data_processor, csv_factory_chs_cbo):
        custom_data = ["6990193", "350750", "USF COHAB IV BOTUCATU", "40", "MEDICO CLINICO", "202303"]

        csv_file = csv_factory_chs_cbo(data=custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert valid_months == 3
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert overall_result["in-memory-data"]["pending"] == 45

    def test_process_csv_valid_clinicals(self, data_processor, csv_factory_chs_cbo):
        custom_data = ["6990193", "350750", "USF COHAB IV BOTUCATU", "40", "MEDICO CLINICOS", "202303"]

        csv_file = csv_factory_chs_cbo(data=custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert valid_months == 3
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert overall_result["in-memory-data"]["pending"] == 45

    def test_process_csv_valid_generalist(self, data_processor, csv_factory_chs_cbo):
        custom_data = ["6990193", "350750", "USF COHAB IV BOTUCATU", "40", "MEDICOS GENERALISTA", "202303"]

        csv_file = csv_factory_chs_cbo(data=custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert valid_months == 3
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert overall_result["in-memory-data"]["pending"] == 45
