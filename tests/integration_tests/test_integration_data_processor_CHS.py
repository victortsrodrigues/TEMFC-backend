import pytest
import math
from src.core.services.data_processor import DataProcessor
from src.core.services.establishment_validator import EstablishmentValidator
from src.repositories.establishment_repository import EstablishmentRepository
from src.interfaces.web_scraper import CNESScraper


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
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "8",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            }
        ]

        test_csv_path = csv_factory_chs_cbo(data=custom_data)

        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)

        # Assertions
        assert math.isclose(valid_months, 2)
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]["status"] == "Not eligible"
        assert math.isclose(overall_result[str(test_csv_path)]["pending"], 46)

    def test_process_csv_overlap_40(self, data_processor, csv_factory_chs_cbo):
        """Simulate overlap of months with at least one month with CHS > 40. Should be valid only one occurrency of 40"""
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "40",
                "DESCRICAO CBO": "MEDICO DA FAMILIA",
                "COMP.": "02/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "30",
                "DESCRICAO CBO": "MEDICO DA FAMILIA",
                "COMP.": "02/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "20",
                "DESCRICAO CBO": "MEDICO DA FAMILIA",
                "COMP.": "02/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "10",
                "DESCRICAO CBO": "MEDICO DA FAMILIA",
                "COMP.": "02/2023",
            },
        ]

        test_csv_path = csv_factory_chs_cbo(data=custom_data)

        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)

        # Assertions
        assert valid_months == 2
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]["status"] == "Not eligible"
        assert overall_result[str(test_csv_path)]["pending"] == 46

    def test_process_csv_chs_30(self, data_processor, csv_factory_chs_cbo):
        """Simulate CHS = 30. Should be 2.75 valid months"""
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "30",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            }
        ]

        test_csv_path = csv_factory_chs_cbo(data=custom_data)

        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)

        # Assertions
        assert math.isclose(valid_months, 2.75)
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]["status"] == "Not eligible"
        assert math.isclose(overall_result[str(test_csv_path)]["pending"], 45.25)

    def test_process_csv_overlap_chs_30(self, data_processor, csv_factory_chs_cbo):
        """Simulate CHS = 30. Should promote to 40 and be valid 3 months"""
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "30",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "30",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
        ]

        test_csv_path = csv_factory_chs_cbo(data=custom_data)

        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)

        # Assertions
        assert math.isclose(valid_months, 3)
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]["status"] == "Not eligible"
        assert math.isclose(overall_result[str(test_csv_path)]["pending"], 45)

    def test_process_csv_overlap_chs_30_and_20(self, data_processor, csv_factory_chs_cbo):
        """Should promote to 40 and be valid 3 months"""
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "30",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "20",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
        ]

        test_csv_path = csv_factory_chs_cbo(data=custom_data)

        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)

        # Assertions
        assert math.isclose(valid_months, 3)
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]["status"] == "Not eligible"
        assert math.isclose(overall_result[str(test_csv_path)]["pending"], 45)

    def test_process_csv_overlap_chs_30_and_10(self, data_processor, csv_factory_chs_cbo):
        """Should promote to 40 and be valid 3 months"""
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "30",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "10",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
        ]

        test_csv_path = csv_factory_chs_cbo(data=custom_data)

        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)

        # Assertions
        assert math.isclose(valid_months, 3)
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]["status"] == "Not eligible"
        assert math.isclose(overall_result[str(test_csv_path)]["pending"], 45)

    def test_process_csv_chs_20(self, data_processor, csv_factory_chs_cbo):
        """Simulate CHS = 20"""
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "20",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            }
        ]

        test_csv_path = csv_factory_chs_cbo(data=custom_data)

        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)

        # Assertions
        assert math.isclose(valid_months, 2.5)
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]["status"] == "Not eligible"
        assert math.isclose(overall_result[str(test_csv_path)]["pending"], 45.5)

    def test_process_csv_overlap_chs_20(self, data_processor, csv_factory_chs_cbo):
        """should promote to 40 and be valid 3 months"""
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "20",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "20",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "20",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
        ]

        test_csv_path = csv_factory_chs_cbo(data=custom_data)

        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)

        # Assertions
        assert math.isclose(valid_months, 3)
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]["status"] == "Not eligible"
        assert math.isclose(overall_result[str(test_csv_path)]["pending"], 45)

    def test_process_csv_overlap_chs_20_and_10(self, data_processor, csv_factory_chs_cbo):
        """should promote to 30 and be valid 2.75 months"""
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "20",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "10",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
        ]

        test_csv_path = csv_factory_chs_cbo(data=custom_data)

        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)

        # Assertions
        assert math.isclose(valid_months, 2.75)
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]["status"] == "Not eligible"
        assert math.isclose(overall_result[str(test_csv_path)]["pending"], 45.25)

    def test_process_csv_chs_10(self, data_processor, csv_factory_chs_cbo):
        """Simulate CHS = 10. Shouldn't count. Should be valid 2 months"""
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "10",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            }
        ]

        test_csv_path = csv_factory_chs_cbo(data=custom_data)

        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)

        # Assertions
        assert math.isclose(valid_months, 2)
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]["status"] == "Not eligible"
        assert math.isclose(overall_result[str(test_csv_path)]["pending"], 46)

    def test_process_csv_double_overlap_chs_10(self, data_processor, csv_factory_chs_cbo):
        """Should promote to 20 and be valid 2.5 months"""
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "10",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "10",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
        ]

        test_csv_path = csv_factory_chs_cbo(data=custom_data)

        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)

        # Assertions
        assert math.isclose(valid_months, 2.5)
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]["status"] == "Not eligible"
        assert math.isclose(overall_result[str(test_csv_path)]["pending"], 45.5)


    def test_process_csv_triple_overlap_chs_10(self, data_processor, csv_factory_chs_cbo):
        """Should promote to 30 and be valid 2.75 months"""
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "10",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "10",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "10",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
        ]

        test_csv_path = csv_factory_chs_cbo(data=custom_data)

        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)

        # Assertions
        assert math.isclose(valid_months, 2.75)
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]["status"] == "Not eligible"
        assert math.isclose(overall_result[str(test_csv_path)]["pending"], 45.25)


    def test_process_csv_quadra_overlap_chs_10(self, data_processor, csv_factory_chs_cbo):
        """Should promote to 40 and be valid 3 months"""
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "10",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "10",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "10",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "10",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023",
            },
        ]

        test_csv_path = csv_factory_chs_cbo(data=custom_data)

        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)

        # Assertions
        assert math.isclose(valid_months, 3)
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]["status"] == "Not eligible"
        assert math.isclose(overall_result[str(test_csv_path)]["pending"], 45)