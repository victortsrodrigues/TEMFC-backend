from .base_error import BaseError

class NotFoundError(BaseError):
    """Resource not found errors"""
    def __init__(self, message, details=None):
      super().__init__(message, status_code=404, details=details)