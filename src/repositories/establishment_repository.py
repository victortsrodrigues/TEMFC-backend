import sqlite3
import logging
from config.settings import settings
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

class EstablishmentRepository:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def check_establishment(self, ibge_cnes):
        try:
            # Check serv159152 table (equivalent to valid CNES)
            with settings.engine.connect() as conn:
                result = conn.execute(
                    text('SELECT COUNT(*) FROM serv159152 WHERE "CO_UNIDADE" = :val'),
                    {"val": ibge_cnes}
                ).fetchone()
                if result[0] > 0:
                    return True
                
                # Check all_estab_serv_class table (equivalent to general CNES)
                result = conn.execute(
                    text('SELECT COUNT(*) FROM all_estab_serv_class WHERE "CO_UNIDADE" = :val'),
                    {"val": ibge_cnes}
                ).fetchone()

                return False if result[0] > 0 else None
        
        except SQLAlchemyError as e:
            self.logger.error(f"Database error: {str(e)}")
            return None