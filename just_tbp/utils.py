# just_tbp/utils.py
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Sequence
from urllib.parse import quote_plus  # For magnet links
from .models import Torrent, TorrentDetails, FileEntry
from .exceptions import TPBContentError  # Assuming you might need this

# Default trackers for magnet links (can be overridden)
DEFAULT_TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.stealth.si:80/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://tracker.bittor.pw:1337/announce",
    "udp://public.popcorn-tracker.org:6969/announce",
    "udp://tracker.dler.org:6969/announce",
    "udp://exodus.desync.com:6969/announce",
    "udp://open.demonii.com:1337/announce",  # Note: demonii might be offline
]


def _parse_common_torrent_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to parse common fields for Torrent and TorrentDetails."""
    try:
        added_ts = int(data.get("added", 0))
        # Handle potential huge numbers if API returns milliseconds or invalid data
        if added_ts > 253402300799:  # Max valid timestamp (year 9999)
            added_ts //= 1000  # Assume milliseconds if too large

        parsed = {
            "id": int(data.get("id", 0)),
            "name": data.get("name", ""),
            "info_hash": data.get("info_hash", "").lower(),  # Hashes are case-insensitive but usually lowercase
            "leechers": int(data.get("leechers", 0)),
            "seeders": int(data.get("seeders", 0)),
            "num_files": int(data.get("num_files", 0)),
            "size": int(data.get("size", 0)),
            "username": data.get("username", "Anonymous"),
            "added": datetime.fromtimestamp(added_ts, tz=timezone.utc),
            "status": data.get("status", ""),
            "category": int(data.get("category", 0)),  # type: ignore
            "imdb": data.get("imdb") if data.get("imdb") and str(data.get("imdb")).strip() else None,
        }
        return parsed
    except (ValueError, TypeError) as e:
        raise TPBContentError(f"Error parsing common torrent fields: {e}. Data: {data}") from e


def parse_torrent_list(api_response: List[Dict[str, Any]]) -> List[Torrent]:
    torrents: List[Torrent] = []
    if not api_response:
        return torrents

    if len(api_response) == 1 and api_response[0].get("name") == "No results returned":
        return torrents

    for item_data in api_response:
        try:
            common_fields = _parse_common_torrent_fields(item_data)
            torrents.append(Torrent(**common_fields))
        except TPBContentError as e:
            print(f"Skipping torrent due to parsing error: {e}")  # Or log instead of print
            continue
    return torrents


def parse_torrent_details(api_response: Dict[str, Any]) -> Optional[TorrentDetails]:
    if not api_response:
        return None
    if api_response.get("name") == "Torrent does not exsist.":  # Sic
        return None

    try:
        common_fields = _parse_common_torrent_fields(api_response)

        details_fields = {
            "descr": api_response.get("descr", ""),
            "language": api_response.get("language") if api_response.get("language") else None,
            "text_language": api_response.get("textLanguage") if api_response.get("textLanguage") else None,
        }
        all_fields = {**common_fields, **details_fields}

        # Explicitly map to ensure all fields are present for TorrentDetails constructor
        return TorrentDetails(
            id=all_fields["id"],
            name=all_fields["name"],
            info_hash=all_fields["info_hash"],
            leechers=all_fields["leechers"],
            seeders=all_fields["seeders"],
            num_files=all_fields["num_files"],
            size=all_fields["size"],
            username=all_fields["username"],
            added=all_fields["added"],
            status=all_fields["status"],
            category=all_fields["category"],  # type: ignore
            imdb=all_fields.get("imdb"),
            descr=all_fields["descr"],
            language=all_fields.get("language"),
            text_language=all_fields.get("text_language")
        )
    except TPBContentError as e:
        print(f"Skipping torrent details due to parsing error: {e}")  # Or log
        return None
    except (ValueError, TypeError) as e:
        raise TPBContentError(f"Error parsing torrent details fields: {e}. Data: {api_response}") from e


def parse_file_list(api_response: List[Dict[str, List[Any]]]) -> List[FileEntry]:
    """
    Parses the response from /f.php into a list of FileEntry objects.
    The API returns a list of dictionaries, where each key is an internal file ID (ignored)
    and the value is a list containing a sublist: [[filename, filesize_bytes]].
    Example: [{"0": [["file1.txt", 1024]]}, {"1": [["file2.mkv", 204800]]}]
    Sometimes it's just a list of lists: [["file1.txt", 1024], ["file2.mkv", 204800]] (observed with some mirrors)
    """
    files: List[FileEntry] = []
    if not api_response:
        return files

    for item_data in api_response:
        try:
            if isinstance(item_data, dict):  # Standard apibay.org format
                # The actual file info is the first value in the dict
                file_info_list = next(iter(item_data.values()))
                if isinstance(file_info_list, list) and len(file_info_list) > 0:
                    # The first element of this list is another list [name, size]
                    file_details = file_info_list[0]
                    if isinstance(file_details, list) and len(file_details) == 2:
                        name = str(file_details[0])
                        size = int(file_details[1])
                        files.append(FileEntry(name=name, size=size))
            elif isinstance(item_data, list) and len(item_data) == 2:  # Simpler list format
                name = str(item_data[0])
                size = int(item_data[1])
                files.append(FileEntry(name=name, size=size))
        except (IndexError, ValueError, TypeError, StopIteration) as e:
            print(f"Skipping file entry due to parsing error: {e}. Data: {item_data}")  # Or log
            continue
    return files


def generate_magnet_link(info_hash: str, name: str, trackers: Optional[Sequence[str]] = None) -> str:
    """
    Generates a magnet link.

    Args:
        info_hash (str): The info hash of the torrent.
        name (str): The display name for the torrent.
        trackers (Optional[Sequence[str]]): A list of tracker URLs.
                                            Defaults to `DEFAULT_TRACKERS`.

    Returns:
        str: The generated magnet link.
    """
    if trackers is None:
        trackers = DEFAULT_TRACKERS

    magnet_link = f"magnet:?xt=urn:btih:{info_hash.lower()}&dn={quote_plus(name)}"
    for tracker in trackers:
        magnet_link += f"&tr={quote_plus(tracker)}"
    return magnet_link


def format_size(size_bytes: int) -> str:
    """
    Formats a size in bytes to a human-readable string (KiB, MiB, GiB, TiB, PiB).
    """
    if size_bytes < 0: return "N/A"
    if size_bytes == 0: return "0 B"

    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    i = 0
    # Iterate while size is greater than or equal to 1024 and we haven't reached the last unit
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {units[i]}"


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """Formats a datetime object into a string."""
    if not isinstance(dt, datetime):
        return "N/A"
    return dt.strftime(fmt)
