import pytest
from src.core.services.data_processor import DataProcessor
from src.core.services.establishment_validator import EstablishmentValidator
from src.repositories.establishment_repository import EstablishmentRepository
from src.interfaces.web_scraper import CNESScraper

class TestDataProcessorIntegration:
    @pytest.fixture
    def data_processor(self):
        """Create an actual data processor with real dependencies"""
        repo = EstablishmentRepository()
        scraper = CNESScraper()
        establishment_validator = EstablishmentValidator(repo, scraper)
        return DataProcessor(establishment_validator)
      
      
    def test_process_csv_valid_family(self, data_processor, csv_factory):
        """Integration test to verify CSV processing with valid medical professional data"""
        # Create a sample CSV file with realistic medical professional data
        test_csv_path = csv_factory() 
        
        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)
        
        # Assertions
        assert valid_months == 2
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]['status'] == 'Not eligible'
        assert overall_result[str(test_csv_path)]['pending'] == 46
        
    
    def test_process_csv_invalid_cbo(self, data_processor, csv_factory):
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "40",
                "DESCRICAO CBO": "ENFERMEIRO",
                "COMP.": "03/2023"
            }
        ]
        
        test_csv_path = csv_factory(data=custom_data)
        
        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)
        
        # Assertions
        assert valid_months == 2
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]['status'] == 'Not eligible'
        assert overall_result[str(test_csv_path)]['pending'] == 46
        
        
    def test_process_csv_valid_clinical(self, data_processor, csv_factory):
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "40",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "03/2023"
            }
        ]
        
        test_csv_path = csv_factory(data=custom_data)
        
        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)
        
        # Assertions
        assert valid_months == 3
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]['status'] == 'Not eligible'
        assert overall_result[str(test_csv_path)]['pending'] == 45
        
        
    def test_process_csv_valid_clinicals(self, data_processor, csv_factory):
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "40",
                "DESCRICAO CBO": "MEDICOS CLINICO",
                "COMP.": "03/2023"
            }
        ]
        
        test_csv_path = csv_factory(data=custom_data)
        
        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)
        
        # Assertions
        assert valid_months == 3
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]['status'] == 'Not eligible'
        assert overall_result[str(test_csv_path)]['pending'] == 45
        
        
    def test_process_csv_valid_generalist(self, data_processor, csv_factory):
        custom_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "40",
                "DESCRICAO CBO": "MEDICOS GENERALISTA",
                "COMP.": "03/2023"
            }
        ]
        
        test_csv_path = csv_factory(data=custom_data)
        
        # Process the CSV
        overall_result = {}
        valid_months = data_processor.process_csv(test_csv_path, overall_result)
        
        # Assertions
        assert valid_months == 3
        assert str(test_csv_path) in overall_result
        assert overall_result[str(test_csv_path)]['status'] == 'Not eligible'
        assert overall_result[str(test_csv_path)]['pending'] == 45