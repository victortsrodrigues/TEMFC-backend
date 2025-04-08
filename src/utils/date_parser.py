from datetime import datetime

class DateParser:        
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
            raise ValueError(f"Formato de data inválido: {date_str}")
        
        year = date_str[:4]
        month = date_str[4:]
        
        if not (1 <= int(month) <= 12):
            raise ValueError(f"Mês inválido: {date_str}")
        
        return f"{month}/{year}"