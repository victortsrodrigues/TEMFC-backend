from .not_found_error import NotFoundError

class CSVScrapingError(NotFoundError):
    """CSV scraping specific errors"""
    def __init__(self, message, details=None):
        super().__init__(message, details)