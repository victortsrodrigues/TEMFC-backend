import pytest

from src.core.services.establishment_validator import EstablishmentValidator
from src.repositories.establishment_repository import EstablishmentRepository
from interfaces.establishment_scraper import CNESScraper


class TestDataProcessorEstablishmentIntegration:
    @pytest.fixture
    def establishment_validator(self):
        """Create an actual establishment validator with real dependencies"""
        repo = EstablishmentRepository()
        scraper = CNESScraper()
        return EstablishmentValidator(repo, scraper)
      
      
    def test_check_establishment_valid_159(self, establishment_validator, csv_factory_establishment):
        """Should return 159 valid CNES"""

        valid_cnes = establishment_validator.check_establishment(csv_factory_establishment())
        
        # Assertions
        assert '6990193' in valid_cnes
        assert '6644694' in valid_cnes
        
        
    def test_check_establishment_valid_152(self, establishment_validator, csv_factory_establishment):
        """Should return 152 valid CNES"""
        
        custom_data = ["7116438", "110011", "CASA DE APOIO A SAUDE DO INDIO CASAI JARU", "40", "MEDICO CLINICO", "202303"]
        
        valid_cnes = establishment_validator.check_establishment(csv_factory_establishment(data=custom_data))
        
        # Assertions
        assert '6990193' in valid_cnes
        assert '6644694' in valid_cnes
        assert '7116438' in valid_cnes
        
    # @pytest.mark.skip(reason="Takes too long. Temporary skip")
    def test_check_establishment_web(self, establishment_validator, csv_factory_establishment):
        """Should search in the web"""
        
        custom_data = ["9901124", "241105", "MEDNORTH", "40", "MEDICO CLINICO", "202303"]
        
        valid_cnes = establishment_validator.check_establishment(csv_factory_establishment(data=custom_data))
        
        # Assertions
        assert '6990193' in valid_cnes
        assert '6644694' in valid_cnes
        assert '9901124' not in valid_cnes
        
    # @pytest.mark.skip(reason="Takes too long. Temporary skip")    
    def test_check_establishment_web_and_dont_find(self, establishment_validator, csv_factory_establishment):
        """Should search in the web"""
        
        custom_data = ["999999", "111111", "FULANO", "40", "MEDICO CLINICO", "202303"]
        
        valid_cnes = establishment_validator.check_establishment(csv_factory_establishment(data=custom_data))
        
        # Assertions
        assert '6990193' in valid_cnes
        assert '6644694' in valid_cnes
        assert '999999' not in valid_cnes