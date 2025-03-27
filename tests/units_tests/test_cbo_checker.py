import pytest
from src.utils.cbo_checker import CBOChecker

# Unit Tests
class TestCBOChecker:
    def test_contains_clinico_terms(self):
        """Test identification of clinico-related job descriptions"""
        assert CBOChecker.contains_clinico_terms("MEDICO CLINICO") == True
        assert CBOChecker.contains_clinico_terms("MEDICOS CLINICO") == True
        assert CBOChecker.contains_clinico_terms("ENFERMEIRO") == False
    
    def test_contains_generalista_terms(self):
        """Test identification of generalist job descriptions"""
        assert CBOChecker.contains_generalista_terms("MEDICO CLINICO") == False
        assert CBOChecker.contains_generalista_terms("MEDICO GENERALISTA") == True
    
    def test_contains_familia_terms(self):
        """Test identification of family medicine job descriptions"""
        assert CBOChecker.contains_familia_terms("MEDICO DA ESTRATEGIA DE SAUDE DA FAMILIA") == True
        assert CBOChecker.contains_familia_terms("MEDICO CLINICO") == False