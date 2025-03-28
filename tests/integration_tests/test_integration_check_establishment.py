import pytest
import csv
from src.core.services.data_processor import DataProcessor
from src.core.services.establishment_validator import EstablishmentValidator
from src.repositories.establishment_repository import EstablishmentRepository
from src.interfaces.web_scraper import CNESScraper


class TestDataProcessorEstablishmentIntegration:
    @pytest.fixture
    def establishment_validator(self):
        """Create an actual establishment validator with real dependencies"""
        repo = EstablishmentRepository()
        scraper = CNESScraper()
        return EstablishmentValidator(repo, scraper)
      
      
    def test_check_establishment_valid_159(self, establishment_validator, csv_factory_establishment):
        """Should return 159 valid CNES"""
        # Create a sample CSV file with realistic medical professional data
        test_csv_path = csv_factory_establishment() 
        
        # Open the CSV and run validation
        with open(test_csv_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter=';')
            valid_cnes = establishment_validator.check_establishment(csv_reader)
        
        # Assertions
        assert '6990193' in valid_cnes
        assert '6644694' in valid_cnes
        
        
    def test_check_establishment_valid_152(self, establishment_validator, csv_factory_establishment):
        """Should return 152 valid CNES"""
        
        custom_data = [
            {
                "CNES": "7116438",
                "IBGE": "110011",
                "ESTABELECIMENTO": "CASA DE APOIO A SAUDE DO INDIO CASAI JARU",
                "CHS AMB.": "40",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "01/2023"
            },
        ]
        
        test_csv_path = csv_factory_establishment(data=custom_data) 
        
        # Open the CSV and run validation
        with open(test_csv_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter=';')
            valid_cnes = establishment_validator.check_establishment(csv_reader)
        
        # Assertions
        assert '6990193' in valid_cnes
        assert '6644694' in valid_cnes
        assert '7116438' in valid_cnes
        
    @pytest.mark.skip(reason="Takes too long. Temporary skip")
    def test_check_establishment_web(self, establishment_validator, csv_factory_establishment):
        """Should search in the web"""
        
        custom_data = [
            {
                "CNES": "9901124",
                "IBGE": "241105",
                "ESTABELECIMENTO": "MEDNORTH",
                "CHS AMB.": "40",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "01/2023"
            },
        ]
        
        test_csv_path = csv_factory_establishment(data=custom_data) 
        
        # Open the CSV and run validation
        with open(test_csv_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter=';')
            valid_cnes = establishment_validator.check_establishment(csv_reader)
        
        # Assertions
        assert '6990193' in valid_cnes
        assert '6644694' in valid_cnes
        assert '9901124' not in valid_cnes
        
    @pytest.mark.skip(reason="Takes too long. Temporary skip")    
    def test_check_establishment_web_and_dont_find(self, establishment_validator, csv_factory_establishment):
        """Should search in the web"""
        
        custom_data = [
            {
                "CNES": "999999",
                "IBGE": "111111",
                "ESTABELECIMENTO": "FULANO",
                "CHS AMB.": "40",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "01/2023"
            },
        ]
        
        test_csv_path = csv_factory_establishment(data=custom_data) 
        
        # Open the CSV and run validation
        with open(test_csv_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile, delimiter=';')
            valid_cnes = establishment_validator.check_establishment(csv_reader)
        
        # Assertions
        assert '6990193' in valid_cnes
        assert '6644694' in valid_cnes
        assert '999999' not in valid_cnes