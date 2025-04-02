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
            with settings.engine.connect() as conn:
                # Check if estab exists in all_estab_serv_class table
                result = conn.execute(
                    text('SELECT COUNT(*) FROM all_estab_serv_class WHERE "CO_UNIDADE" = :val'),
                    {"val": ibge_cnes}
                ).fetchone()
                estab_exists_in_all_estab_serv_class = result[0] > 0
                if estab_exists_in_all_estab_serv_class:
                    result = conn.execute(
                        text('SELECT COUNT(*) FROM all_estab_serv_class WHERE "CO_UNIDADE" = :val AND "CO_SERVICO" IN (159, 152)'),
                        {"val": ibge_cnes}
                    ).fetchone()
                    return True if result[0] > 0 else False
                    
                else:
                    return None
                        
        except SQLAlchemyError as e:
            self.logger.error(f"Database error: {str(e)}")
            return None