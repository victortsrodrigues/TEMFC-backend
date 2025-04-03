from .base_error import BaseError

class DataProcessingError(BaseError):
    """Data processing errors"""
    def __init__(self, message, details=None):
        super().__init__(message, status_code=422, details=details)