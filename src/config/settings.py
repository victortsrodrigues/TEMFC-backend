import os

class Settings:
    def __init__(self):
        self.BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
        self.DATABASES = {
            'valid_cnes_db_path': self.BASE_DIR + '\\databases' + '\\estab_202411_159_152.db',
            'general_cnes_db_path': self.BASE_DIR + '\\databases' + '\\estabelecimentos_202411.db'
        }
        self.ASSETS_DIR = self.BASE_DIR + '\\assets'
        self.REPORTS_DIR = self.BASE_DIR + '\\reports'
        self.CHROME_OPTIONS = [
            "--headless",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]

    def get_database_path(self, key: str) -> str:
        """Get database path as string for SQLite compatibility"""
        return str(self.DATABASES[key])
    
settings = Settings()