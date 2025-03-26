import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
        self.VALID_CNES_DB_FILENAME = os.getenv('VALID_CNES_DB_FILENAME')
        self.GENERAL_CNES_DB_FILENAME = os.getenv('GENERAL_CNES_DB_FILENAME')
        if not self.VALID_CNES_DB_FILENAME or not self.GENERAL_CNES_DB_FILENAME:
            raise ValueError("Missing database filenames in .env file")
        self.DATABASES = {
            'valid_cnes_db_path': os.path.join(self.BASE_DIR, 'databases', os.getenv('VALID_CNES_DB_FILENAME')),
            'general_cnes_db_path': os.path.join(self.BASE_DIR, 'databases', os.getenv('GENERAL_CNES_DB_FILENAME'))
        }
        self.ASSETS_DIR = os.path.join(self.BASE_DIR, 'assets')
        self.REPORTS_DIR = os.path.join(self.BASE_DIR, 'reports')
        self.CHROME_OPTIONS = [
            "--headless",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]

    def get_database_path(self, key: str) -> str:
        """Get database path as string for SQLite compatibility"""
        return str(self.DATABASES[key])
    
settings = Settings()