# just_tbp/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from .constants import CategoryId


@dataclass
class Torrent:
    id: int
    name: str
    info_hash: str
    leechers: int
    seeders: int
    num_files: int
    size: int  # Size in bytes
    username: str
    added: datetime
    status: str
    category: CategoryId
    imdb: Optional[str] = None  # Can be empty string from API, normalized to None


@dataclass
class TorrentDetails:
    id: int
    name: str
    info_hash: str
    leechers: int
    seeders: int
    num_files: int
    size: int  # Size in bytes
    username: str
    added: datetime  # Unix timestamp from API, converted
    status: str
    category: CategoryId  # Numerical ID
    descr: str
    imdb: Optional[str] = None
    language: Optional[str] = None
    text_language: Optional[str] = None


@dataclass
class FileEntry:
    name: str
    size: int


SearchResults = List[Torrent]
TorrentResults = List[Torrent]  # Alias for consistency with TS
