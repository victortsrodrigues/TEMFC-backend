import pytest
from datetime import datetime
from src.utils.date_parser import DateParser

# Unit Tests
class TestDateParser:
    def test_parse_standard_format(self):
        """Test parsing dates in standard format"""
        assert DateParser.parse("01/2025") == datetime(2025, 1, 1)
    
    def test_parse_abbreviated_month(self):
        """Test parsing dates with abbreviated months"""
        assert DateParser.parse("jan/25") == datetime(2025, 1, 1)
    
    def test_parse_invalid_date(self):
        """Test handling of invalid date formats"""
        with pytest.raises(ValueError):
            DateParser.parse("invalid/date")