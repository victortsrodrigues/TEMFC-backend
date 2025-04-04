from .base_error import BaseError

class EstablishmentValidationError(BaseError):
    """Establishment validation related errors (CNES/establishment validation failures)"""
    def __init__(self, message, details=None):
        super().__init__(message, status_code=422, details=details)