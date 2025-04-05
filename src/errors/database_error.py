from .base_error import BaseError

class DatabaseError(BaseError):
    """Database connection and query errors"""
    def __init__(self, message, details=None):
        super().__init__(message, status_code=500, details=details)