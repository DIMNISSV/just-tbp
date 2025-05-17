# just_tbp/exceptions.py
class TPBRequestError(Exception):
    """Custom exception for API request errors."""
    pass


class TPBContentError(Exception):
    """Custom exception for errors related to API content (e.g., torrent not found)."""
    pass
