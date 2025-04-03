from .base_error import BaseError

class ValidationError(BaseError):
    """Input validation errors"""
    def __init__(self, message, details=None):
        super().__init__(message, status_code=400, details=details)