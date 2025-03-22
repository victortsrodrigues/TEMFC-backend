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