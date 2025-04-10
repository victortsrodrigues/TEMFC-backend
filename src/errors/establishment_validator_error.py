from .base_error import BaseError

class EstablishmentValidationError(BaseError):
    def __init__(self, message, details=None):
        super().__init__(message, status_code=422, details=details)