import pytest
import math
from src.core.services.data_processor import DataProcessor
from src.core.services.establishment_validator import EstablishmentValidator
from src.repositories.establishment_repository import EstablishmentRepository
from interfaces.establishment_scraper import CNESScraper


class TestDataProcessorCHSIntegration:
    @pytest.fixture
    def data_processor(self):
        """Create an actual data processor with real dependencies"""
        repo = EstablishmentRepository()
        scraper = CNESScraper()
        establishment_validator = EstablishmentValidator(repo, scraper)
        return DataProcessor(establishment_validator)

    def test_process_csv_invalid_chs(self, data_processor, csv_factory_chs_cbo):
        """Should not be valid. Should be 2 valid months"""
        custom_data = [
            "6990193",
            "350750",
            "USF COHAB IV BOTUCATU",
            "8",
            "MEDICO CLINICO",
            "202303",
        ]

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

    def test_process_csv_overlap_40(self, data_processor, csv_factory_chs_cbo):
        """Simulate overlap of months with at least one month with CHS > 40. Should be valid only one occurrency of 40"""
        custom_data = [
            "6990193",
            "350750",
            "USF COHAB IV BOTUCATU",
            "40",
            "MEDICO DA FAMILIA",
            "202302",
        ]

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

    def test_process_csv_chs_30(self, data_processor, csv_factory_chs_cbo):
        """Simulate CHS = 30. Should be 2.75 valid months"""
        custom_data = [
            "6990193",
            "350750",
            "USF COHAB IV BOTUCATU",
            "30",
            "MEDICO DA FAMILIA",
            "202303",
        ]

        csv_file = csv_factory_chs_cbo(data=custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert math.isclose(valid_months, 2.75)
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert math.isclose(overall_result["in-memory-data"]["pending"], 45.25)

    def test_process_csv_overlap_chs_30(self, data_processor, csv_factory_chs_cbo_clear):
        """Simulate CHS = 30. Should promote to 40 and be valid 3 months"""
        custom_data = [
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "30",
                "MEDICO CLINICO",
                "202303",
            ],
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "30",
                "MEDICO CLINICO",
                "202303",
            ],
        ]

        csv_file = csv_factory_chs_cbo_clear(custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert math.isclose(valid_months, 1)
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert math.isclose(overall_result["in-memory-data"]["pending"], 47)

    def test_process_csv_overlap_chs_30_and_20(
        self, data_processor, csv_factory_chs_cbo_clear
    ):
        """Should promote to 40 and be valid 3 months"""
        custom_data = [
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "30",
                "MEDICO CLINICO",
                "202303",
            ],
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "20",
                "MEDICO CLINICO",
                "202303",
            ],
        ]

        csv_file = csv_factory_chs_cbo_clear(custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert math.isclose(valid_months, 1)
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert math.isclose(overall_result["in-memory-data"]["pending"], 47)

    def test_process_csv_overlap_chs_30_and_10(
        self, data_processor, csv_factory_chs_cbo_clear
    ):
        """Should promote to 40 and be valid 3 months"""
        custom_data = [
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "30",
                "MEDICO CLINICO",
                "202303",
            ],
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "10",
                "MEDICO CLINICO",
                "202303",
            ],
        ]

        csv_file = csv_factory_chs_cbo_clear(custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert math.isclose(valid_months, 1)
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert math.isclose(overall_result["in-memory-data"]["pending"], 47)

    def test_process_csv_chs_20(self, data_processor, csv_factory_chs_cbo_clear):
        """Simulate CHS = 20"""
        custom_data = [
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "20",
                "MEDICO CLINICO",
                "202303",
            ]
        ]

        csv_file = csv_factory_chs_cbo_clear(custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert math.isclose(valid_months, 0.5)
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert math.isclose(overall_result["in-memory-data"]["pending"], 47.5)

    def test_process_csv_overlap_chs_20(self, data_processor, csv_factory_chs_cbo_clear):
        """should promote to 40 and be valid 3 months"""
        custom_data = [
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "20",
                "MEDICO CLINICO",
                "202303",
            ],
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "20",
                "MEDICO CLINICO",
                "202303",
            ],
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "20",
                "MEDICO CLINICO",
                "202303",
            ],
        ]

        csv_file = csv_factory_chs_cbo_clear(custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert math.isclose(valid_months, 1)
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert math.isclose(overall_result["in-memory-data"]["pending"], 47)

    def test_process_csv_overlap_chs_20_and_10(
        self, data_processor, csv_factory_chs_cbo_clear
    ):
        """should promote to 30 and be valid 0.75 months"""
        custom_data = [
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "20",
                "MEDICO CLINICO",
                "202303",
            ],
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "10",
                "MEDICO CLINICO",
                "202303",
            ],
        ]

        csv_file = csv_factory_chs_cbo_clear(custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert math.isclose(valid_months, 0.75)
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert math.isclose(overall_result["in-memory-data"]["pending"], 47.25)

    def test_process_csv_chs_10(self, data_processor, csv_factory_chs_cbo_clear):
        """Simulate CHS = 10. Shouldn't count. Should be valid 2 months"""
        custom_data = [
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "10",
                "MEDICO CLINICO",
                "202303",
            ]
        ]

        csv_file = csv_factory_chs_cbo_clear(custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert valid_months == 0
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert math.isclose(overall_result["in-memory-data"]["pending"], 48)

    def test_process_csv_double_overlap_chs_10(
        self, data_processor, csv_factory_chs_cbo_clear
    ):
        """Should promote to 20 and be valid 2.5 months"""
        custom_data = [
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "10",
                "MEDICO CLINICO",
                "202303",
            ],
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "10",
                "MEDICO CLINICO",
                "202303",
            ],
        ]

        csv_file = csv_factory_chs_cbo_clear(custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert math.isclose(valid_months, 0.5)
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert math.isclose(overall_result["in-memory-data"]["pending"], 47.5)

    def test_process_csv_triple_overlap_chs_10(
        self, data_processor, csv_factory_chs_cbo_clear
    ):
        """Should promote to 30 and be valid 0.75 months"""
        custom_data = [
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "10",
                "MEDICO CLINICO",
                "202303",
            ],
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "10",
                "MEDICO CLINICO",
                "202303",
            ],
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "10",
                "MEDICO CLINICO",
                "202303",
            ],
        ]

        csv_file = csv_factory_chs_cbo_clear(custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert math.isclose(valid_months, 0.75)
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert math.isclose(overall_result["in-memory-data"]["pending"], 47.25)

    def test_process_csv_quadra_overlap_chs_10(
        self, data_processor, csv_factory_chs_cbo_clear
    ):
        """Should promote to 40 and be valid 1 months"""
        custom_data = [
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "10",
                "MEDICO CLINICO",
                "202303",
            ],
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "10",
                "MEDICO CLINICO",
                "202303",
            ],
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "10",
                "MEDICO CLINICO",
                "202303",
            ],
            [
                "6990193",
                "350750",
                "USF COHAB IV BOTUCATU",
                "10",
                "MEDICO CLINICO",
                "202303",
            ],
        ]

        csv_file = csv_factory_chs_cbo_clear(custom_data)
        overall_result = {}
        body = {"name": "in-memory-data"}

        # Process the CSV
        valid_months = data_processor.process_csv(csv_file, overall_result, body)

        # Assertions
        assert math.isclose(valid_months, 1)
        assert "in-memory-data" in overall_result
        assert overall_result["in-memory-data"]["status"] == "Not eligible"
        assert math.isclose(overall_result["in-memory-data"]["pending"], 47)