from datetime import datetime

class DateParser:
    @staticmethod
    def parse(date_str):
        try:
            return datetime.strptime(date_str, "%m/%Y")
        except ValueError:
            pass
            
        months = {
            "jan": "01", "fev": "02", "mar": "03", "abr": "04",
            "mai": "05", "jun": "06", "jul": "07", "ago": "08",
            "set": "09", "out": "10", "nov": "11", "dez": "12"
        }
        
        try:
            month_abbr, year = date_str.split("/")
            return datetime.strptime(f"{months[month_abbr.lower()]}/20{year}", "%m/%Y")
        except Exception:
            raise ValueError(f"Invalid date format: {date_str}")
        
    @staticmethod
    def format_yyyymm_to_mm_yyyy(date_str: str) -> str:
        """
        Converts a date string in 'YYYYMM' format to 'MM/YYYY'.
        
        Args:
            date_str (str): Input date string (e.g., '202312').
            
        Returns:
            str: Formatted date string (e.g., '12/2023').
            
        Raises:
            ValueError: If input is invalid.
        """
        if len(date_str) != 6 or not date_str.isdigit():
            raise ValueError(f"Invalid date format: {date_str}")
        
        year = date_str[:4]
        month = date_str[4:]
        
        if not (1 <= int(month) <= 12):
            raise ValueError(f"Invalid month in date: {date_str}")
        
        return f"{month}/{year}"