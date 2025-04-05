import pytest
from datetime import datetime
from src.utils.date_parser import DateParser

# Unit Tests
class TestDateParser:            
    def test_format_yyyymm_to_mm_yyyy_standard_format(self):
        """Test parsing dates in standard format"""
        assert DateParser.format_yyyymm_to_mm_yyyy("202501") == "01/2025"
    
    def test_format_yyyymm_to_mm_yyyy_invalid_date_format(self):
        """Test parsing dates with abbreviated months"""
        with pytest.raises(ValueError):
            DateParser.format_yyyymm_to_mm_yyyy("2025")
    
    def test_format_yyyymm_to_mm_yyyy_invalid_mont_in_date(self):
        """Test handling of invalid date formats"""
        with pytest.raises(ValueError):
            DateParser.format_yyyymm_to_mm_yyyy("202513")