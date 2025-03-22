import sqlite3
import logging
from config.settings import settings

class EstablishmentRepository:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def check_establishment(self, ibge_cnes):
        try:
            with sqlite3.connect(settings.get_database_path('valid_cnes_db_path')) as conn:
                if conn.execute("SELECT 1 FROM serv159152 WHERE valor=?", (ibge_cnes,)).fetchone():
                    return 1
                
            with sqlite3.connect(settings.get_database_path('general_cnes_db_path')) as conn:
                if conn.execute("SELECT 1 FROM tabela_dados WHERE CO_UNIDADE=?", (ibge_cnes,)).fetchone():
                    return 0
                    
            return -1
        
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            return -1