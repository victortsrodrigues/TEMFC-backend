import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Settings:
    """
    Manages application configuration settings, including database and directories.
    """

    def __init__(self):
        """
        Initialize the Settings object and load configuration values.
        """
        self.reload()
    
    def reload(self):
        """
        Reload configuration values from environment variables.
        """
        # PostgreSQL configuration
        self.DB_CONFIG = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD")
        }
        
        # SQLAlchemy engine
        self.engine = create_engine(
            f"postgresql://{self.DB_CONFIG['user']}:{self.DB_CONFIG['password']}"
            f"@{self.DB_CONFIG['host']}:{self.DB_CONFIG['port']}/{self.DB_CONFIG['database']}?sslmode=require"
        )
        
        # Chrome options
        self.CHROME_OPTIONS = [
            "--headless",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]
    
settings = Settings()