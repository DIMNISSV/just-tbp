# just_tbp/client.py
from typing import Optional, Dict, Any

import httpx

from .constants import DEFAULT_BASE_URL, CategoryId, Top100Category
from .exceptions import TPBRequestError, TPBContentError
from .models import TorrentDetails, SearchResults, TorrentResults
from .utils import parse_torrent_list, parse_torrent_details


class TPBClient:
    """
    A Python client for interacting with The Pirate Bay API (apibay.org) using httpx.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        """
        Initializes the TPBClient.

        Args:
            base_url (str, optional): The base URL for the API.
                                      Defaults to "https://apibay.org".
        """
        self.base_url = base_url.rstrip('/')
        # Use httpx.Client for synchronous requests
        self.client = httpx.Client(base_url=self.base_url, headers={"Accept": "application/json"},
                                   follow_redirects=True)

    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Internal method to make HTTP requests to the API.
        """
        # url will be relative to self.client.base_url
        try:
            response = self.client.request(method, endpoint, params=params)
            response.raise_for_status()  # Raises httpx.HTTPStatusError for bad responses (4XX or 5XX)

            if response.text == "false":
                return {}

            return response.json()
        except httpx.HTTPStatusError as e:  # Changed from requests.exceptions.HTTPError
            raise TPBRequestError(f"HTTP error occurred: {e.response.status_code} - {e.response.text}") from e
        except httpx.RequestError as e:  # Changed from requests.exceptions.RequestException
            raise TPBRequestError(f"Request failed: {e}") from e
        except ValueError as e:  # Handles JSONDecodeError if response is not valid JSON
            # httpx.Response.json() raises json.JSONDecodeError which is a subclass of ValueError
            raise TPBContentError(f"Failed to decode JSON response: {e}. Response text: {response.text}") from e

    def search(self, query: str, category_id: Optional[CategoryId] = None) -> SearchResults:
        """
        Search for torrents.

        Args:
            query (str): The search query.
            category_id (Optional[CategoryId]): Numerical category ID to filter by.
                                                See `just_tbp.constants` or `CATEGORIES`.

        Returns:
            SearchResults: A list of Torrent objects.

        Raises:
            TPBRequestError: If the request to the API fails.
            TPBContentError: If the API response is malformed.
        """
        params: Dict[str, Any] = {"q": query}
        if category_id is not None:
            params["cat"] = category_id

        raw_data = self._request("GET", "/q.php", params=params)
        if not isinstance(raw_data, list):
            if isinstance(raw_data, dict) and raw_data.get("error"):
                raise TPBContentError(f"API returned an error: {raw_data.get('error')}")
            if isinstance(raw_data, dict) and not raw_data:  # From "false" response
                return []
            raise TPBContentError(f"Unexpected API response format for search. Expected list, got {type(raw_data)}")
        return parse_torrent_list(raw_data)

    def details(self, torrent_id: int) -> Optional[TorrentDetails]:
        """
        Get details for a specific torrent by its ID.

        Args:
            torrent_id (int): The ID of the torrent.

        Returns:
            Optional[TorrentDetails]: A TorrentDetails object if found, else None.

        Raises:
            TPBRequestError: If the request to the API fails.
            TPBContentError: If the API response is malformed.
        """
        params = {"id": torrent_id}
        raw_data = self._request("GET", "/t.php", params=params)
        if not isinstance(raw_data, dict):
            raise TPBContentError(f"Unexpected API response format for details. Expected dict, got {type(raw_data)}")
        return parse_torrent_details(raw_data)

    def top100(self, category: Top100Category) -> TorrentResults:
        """
        Get the top 100 torrents for a given category or special type.

        Args:
            category (Top100Category): A numerical CategoryId, or "all", or "recent".
                                       See `just_tbp.constants`.

        Returns:
            TorrentResults: A list of Torrent objects.

        Raises:
            TPBRequestError: If the request to the API fails.
            TPBContentError: If the API response is malformed.
        """
        raw_data = self._request("GET", f"/precompiled/data_top100_{category}.json")
        if not isinstance(raw_data, list):
            raise TPBContentError(f"Unexpected API response format for top100. Expected list, got {type(raw_data)}")
        return parse_torrent_list(raw_data)

    def recent(self) -> TorrentResults:
        """
        Get the last 100 recently added torrents.
        This is a shortcut for top100("recent").

        Returns:
            TorrentResults: A list of Torrent objects.

        Raises:
            TPBRequestError: If the request to the API fails.
            TPBContentError: If the API response is malformed.
        """
        return self.top100("recent")

    def by_user(self, username: str, page: int = 0) -> SearchResults:
        """
        Get all torrents uploaded by a specific user.

        Args:
            username (str): The username of the uploader.
            page (int, optional): The page number (0-indexed). Defaults to 0.

        Returns:
            SearchResults: A list of Torrent objects.

        Raises:
            TPBRequestError: If the request to the API fails.
            TPBContentError: If the API response is malformed.
        """
        query = f"user:{username}"
        if page > 0:
            query += f":{page}"

        params = {"q": query}
        raw_data = self._request("GET", "/q.php", params=params)

        if not isinstance(raw_data, list):
            if isinstance(raw_data, dict) and raw_data.get("error"):
                raise TPBContentError(f"API returned an error: {raw_data.get('error')}")
            if isinstance(raw_data, dict) and not raw_data:  # From "false" response
                return []
            raise TPBContentError(f"Unexpected API response format for by_user. Expected list, got {type(raw_data)}")
        return parse_torrent_list(raw_data)

    def set_base_url(self, url: str):
        """
        Change the base URL for the API.
        This will close the current client and create a new one.

        Args:
            url (str): The new base URL.
        """
        self.base_url = url.rstrip('/')
        if hasattr(self, 'client') and self.client is not None:
            self.client.close()  # Close the old client
        self.client = httpx.Client(base_url=self.base_url, headers={"Accept": "application/json"},
                                   follow_redirects=True)

    def close(self):
        """
        Closes the underlying httpx client.
        It's good practice to call this when the TPBClient is no longer needed,
        especially if used in a context where resource cleanup is critical.
        """
        if hasattr(self, 'client') and self.client is not None:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
