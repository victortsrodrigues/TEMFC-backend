import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Settings:
    def __init__(self):
        self.BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
        self.reload()
    
    def reload(self):
        
        # PostgreSQL configuration
        self.DB_CONFIG = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "establishment_db_202502"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "postgres")
        }
        # SQLAlchemy engine
        self.engine = create_engine(
            f"postgresql://{self.DB_CONFIG['user']}:{self.DB_CONFIG['password']}"
            f"@{self.DB_CONFIG['host']}:{self.DB_CONFIG['port']}/{self.DB_CONFIG['database']}"
        )
        
        self.ASSETS_DIR = os.path.join(self.BASE_DIR, 'assets')
        self.REPORTS_DIR = os.path.join(self.BASE_DIR, 'reports')
        self.VALID_CNES_DB_FILENAME = os.getenv('VALID_CNES_DB_FILENAME')
        self.GENERAL_CNES_DB_FILENAME = os.getenv('GENERAL_CNES_DB_FILENAME')
        if not self.VALID_CNES_DB_FILENAME or not self.GENERAL_CNES_DB_FILENAME:
            raise ValueError("Missing database filenames in .env file")
        self.DATABASES = {
            'valid_cnes_db_path': os.path.join(self.BASE_DIR, 'databases', os.getenv('VALID_CNES_DB_FILENAME')),
            'general_cnes_db_path': os.path.join(self.BASE_DIR, 'databases', os.getenv('GENERAL_CNES_DB_FILENAME'))
        }
        self.CHROME_OPTIONS = [
            "--headless",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]

    def get_database_path(self, key: str) -> str:
        """Get database path as string for SQLite compatibility"""
        return str(self.DATABASES[key])
    
settings = Settings()