# just_tbp/utils.py
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from .models import Torrent, TorrentDetails


def _parse_common_torrent_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to parse common fields for Torrent and TorrentDetails."""
    # API returns numbers as strings, convert them
    # API returns 'added' as a string unix timestamp (seconds)
    parsed = {
        "id": int(data.get("id", 0)),
        "name": data.get("name", ""),
        "info_hash": data.get("info_hash", ""),
        "leechers": int(data.get("leechers", 0)),
        "seeders": int(data.get("seeders", 0)),
        "num_files": int(data.get("num_files", 0)),
        "size": int(data.get("size", 0)),
        "username": data.get("username", "Anonymous"),  # Default for safety
        "added": datetime.fromtimestamp(int(data.get("added", 0)), tz=timezone.utc),
        "status": data.get("status", ""),
        "category": int(data.get("category", 0)),
        "imdb": data.get("imdb") if data.get("imdb") else None,
    }
    return parsed


def parse_torrent_list(api_response: List[Dict[str, Any]]) -> List[Torrent]:
    torrents: List[Torrent] = []
    if not api_response:  # Empty list can be valid (e.g. from top100)
        return torrents

    # API returns a list with one item: {'id': '0', 'name': 'No results returned', ...}
    if len(api_response) == 1 and api_response[0].get("name") == "No results returned":
        return torrents  # Return empty list for no results

    for item_data in api_response:
        common_fields = _parse_common_torrent_fields(item_data)
        torrents.append(Torrent(**common_fields))
    return torrents


def parse_torrent_details(api_response: Dict[str, Any]) -> Optional[TorrentDetails]:
    if not api_response:  # Empty dict if API returns nothing
        return None

    # API returns: {'name': 'Torrent does not exsist.'} (sic)
    if api_response.get("name") == "Torrent does not exsist.":
        # Or raise TPBContentError("Torrent does not exist.")
        return None

    common_fields = _parse_common_torrent_fields(api_response)

    # Fields specific to TorrentDetails
    details_fields = {
        "descr": api_response.get("descr", ""),
        "language": api_response.get("language") if api_response.get("language") else None,
        "text_language": api_response.get("textLanguage") if api_response.get("textLanguage") else None,
    }

    # Combine and create TorrentDetails object
    # Mypy might complain here if _parse_common_torrent_fields isn't perfectly aligned,
    # but for dataclasses, it should work if keys match.
    all_fields = {**common_fields, **details_fields}

    # Ensure all required fields for TorrentDetails are present from the combined dict
    # This is more for robustness if API response structure changes slightly
    # or if _parse_common_torrent_fields misses something specific to TorrentDetails
    # that's also in Torrent (which it shouldn't if structured well).
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
