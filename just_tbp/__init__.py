# just_tbp/__init__.py
__version__ = "0.2.0-alpha"

from .async_client import AsyncTPBClient # Changed
from .models import Torrent, TorrentDetails, SearchResults, TorrentResults, FileEntry # Added FileEntry
from .exceptions import TPBRequestError, TPBContentError
from .utils import generate_magnet_link, format_size, format_datetime # Added new utils

# Attempt to import from generated constants, fallback to a placeholder if not found
try:
    from .constants_generated import ( # Or constants.py if you rename it
        CATEGORIES, CategoryId, Top100Category,
        # Add specific category constants if you want to export all of them
        # e.g., AUDIO_MUSIC, VIDEO_MOVIES etc.
        # This can be automated in the generation script or manually listed
    )
except ImportError:
    print("Warning: Generated constants not found. Using placeholder categories.")
    CATEGORIES = {} # type: ignore
    CategoryId = int # type: ignore
    Top100Category = str # type: ignore


__all__ = [
    "AsyncTPBClient",
    "CATEGORIES",
    "CategoryId",
    "Top100Category",
    "Torrent",
    "TorrentDetails",
    "FileEntry",
    "SearchResults",
    "TorrentResults",
    "TPBRequestError",
    "TPBContentError",
    "generate_magnet_link",
    "format_size",
    "format_datetime",
    # Potentially add all individual category constants here too
]