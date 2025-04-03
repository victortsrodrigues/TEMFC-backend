from .base_error import BaseError

class ExternalServiceError(BaseError):
    """External service (scraping, database) errors"""
    def __init__(self, message, details=None):
      super().__init__(message, status_code=503, details=details)