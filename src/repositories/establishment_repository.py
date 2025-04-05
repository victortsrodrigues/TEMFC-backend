import logging
from config.settings import settings
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from errors.database_error import DatabaseError

class EstablishmentRepository:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_establishment(self, ibge_cnes):
        """
        Check if an establishment exists and has specific services
        
        Args:
            ibge_cnes: Combined IBGE and CNES identifier
            
        Returns:
            True: If establishment exists and has service codes 159 or 152
            False: If establishment exists but doesn't have those services
            None: If establishment doesn't exist in database
            
        Raises:
            DatabaseError: If there's a database connection or query error
        """
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
            error_message = f"Database error while checking establishment {ibge_cnes}"
            self.logger.error(f"{error_message}: {str(e)}")
            raise DatabaseError(
                error_message,
                details={
                    "source": "establishment_repository",
                    "operation": "check_establishment",
                    "ibge_cnes": ibge_cnes,
                    "error": str(e)
                }
            )