# just_tbp/async_client.py
import httpx
from typing import List, Optional, Dict, Any, Union

from .constants import DEFAULT_BASE_URL, CategoryId, Top100Category, USER_AGENT
from .models import Torrent, TorrentDetails, SearchResults, TorrentResults, FileEntry
from .exceptions import TPBRequestError, TPBContentError
from .utils import parse_torrent_list, parse_torrent_details, parse_file_list


class AsyncTPBClient:
    """
    An asynchronous Python client for interacting with The Pirate Bay API (apibay.org) using httpx.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL, client: Optional[httpx.AsyncClient] = None):
        """
        Initializes the AsyncTPBClient.

        Args:
            base_url (str, optional): The base URL for the API.
                                      Defaults to "https://apibay.org".
            client (Optional[httpx.AsyncClient], optional): An existing httpx.AsyncClient instance.
                                                            If None, a new one will be created.
        """
        self.base_url = base_url.rstrip('/')
        if client:
            self._client = client
            # Ensure base_url of provided client matches if possible, or at least inform.
            # For simplicity, we'll assume the provided client is configured correctly.
        else:
            # The API sometimes blocks default httpx/python user-agents.
            headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
            self._client = httpx.AsyncClient(base_url=self.base_url, headers=headers, follow_redirects=True)
        self._external_client = client is not None

    async def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Internal method to make HTTP requests to the API.
        """
        try:
            response = await self._client.request(method, endpoint, params=params)
            response.raise_for_status()

            if response.text == "false":  # API can return literal "false" string for some errors
                return {}  # Treat as empty dict to avoid JSON parse error, let parsers handle

            # Handle empty response for file list if it's just an empty string or non-JSON
            if endpoint.startswith("/f.php") and not response.text.strip().startswith(('[', '{')):
                return []  # Empty file list

            return response.json()
        except httpx.HTTPStatusError as e:
            raise TPBRequestError(
                f"HTTP error occurred: {e.response.status_code} for {e.request.url} - {e.response.text}") from e
        except httpx.RequestError as e:
            raise TPBRequestError(f"Request failed for {e.request.url}: {e}") from e
        except ValueError as e:  # Handles JSONDecodeError
            raise TPBContentError(
                f"Failed to decode JSON response for {endpoint}: {e}. Response text: {response.text[:200]}...") from e

    async def search(self, query: str, category_id: Optional[CategoryId] = None, page: int = 0) -> SearchResults:
        """
        Search for torrents.
        The apibay.org API for general search (/q.php) does not officially support pagination beyond
        what it returns by default (usually a limited set). The `page` parameter here is
        more for compatibility with how some TPB sites structure user-specific queries,
        but for general queries, it's often ignored by apibay.org or might lead to no results if non-zero.

        Args:
            query (str): The search query.
            category_id (Optional[CategoryId]): Numerical category ID to filter by.
            page (int, optional): Page number (0-indexed). Its effect on general searches
                                  via apibay.org /q.php is limited. Defaults to 0.

        Returns:
            SearchResults: A list of Torrent objects.
        """
        params: Dict[str, Any] = {"q": query}
        if category_id is not None:
            params["cat"] = category_id
        # The /q.php endpoint of apibay.org doesn't reliably use a 'page' param for general queries.
        # It's more relevant for by_user structured queries.
        # If page > 0, it might result in "No results returned" for general queries.
        # We keep it for potential future API changes or specific query structures.
        if page > 0 and "user:" not in query.lower():  # Only add page if not a user query where page is part of 'q'
            # This behavior is speculative for general /q.php.
            # It's better to assume /q.php returns one page of results.
            # To be safe, we won't add a 'page' parameter here unless the API documentation confirms it.
            # For now, the 'page' in 'user:username:page' is handled within the query string.
            pass

        raw_data = await self._request("GET", "/q.php", params=params)
        if not isinstance(raw_data, list):
            if isinstance(raw_data, dict) and raw_data.get("error"):
                raise TPBContentError(f"API returned an error: {raw_data.get('error')}")
            if isinstance(raw_data, dict) and not raw_data:  # From "false" response
                return []
            raise TPBContentError(f"Unexpected API response format for search. Expected list, got {type(raw_data)}")
        return parse_torrent_list(raw_data)

    async def details(self, torrent_id: int) -> Optional[TorrentDetails]:
        """
        Get details for a specific torrent by its ID.
        """
        params = {"id": torrent_id}
        raw_data = await self._request("GET", "/t.php", params=params)
        if not isinstance(raw_data, dict):
            raise TPBContentError(f"Unexpected API response format for details. Expected dict, got {type(raw_data)}")
        return parse_torrent_details(raw_data)

    async def top100(self, category: Top100Category, page: Optional[int] = None) -> TorrentResults:
        """
        Get the top 100 torrents for a given category or special type.
        Pagination for "recent" might be supported via different filenames (e.g., data_top100_recent_1.json).

        Args:
            category (Top100Category): A numerical CategoryId, "all", or "recent".
            page (Optional[int]): Page number (0-indexed). Primarily for "recent" if API supports it.

        Returns:
            TorrentResults: A list of Torrent objects.
        """
        endpoint = f"/precompiled/data_top100_{category}.json"
        if category == "recent" and page is not None and page > 0:
            endpoint = f"/precompiled/data_top100_recent_{page}.json"

        raw_data = await self._request("GET", endpoint)
        if not isinstance(raw_data, list):
            raise TPBContentError(f"Unexpected API response format for top100. Expected list, got {type(raw_data)}")
        return parse_torrent_list(raw_data)

    async def recent(self, page: Optional[int] = None) -> TorrentResults:
        """
        Get the last 100 recently added torrents, potentially paginated.
        """
        return await self.top100("recent", page=page)

    async def by_user(self, username: str, page: int = 0, period: Optional[str] = None) -> SearchResults:
        """
        Get torrents by a specific user, optionally paginated or filtered by period.
        The query format is `user:<username>:<page>:<period_filter>`.

        Args:
            username (str): The username.
            page (int, optional): The page number (0-indexed). Defaults to 0.
            period (Optional[str]): Time period filter e.g. "today", "twodays".

        Returns:
            SearchResults: A list of Torrent objects.
        """
        query_parts = [f"user:{username}"]
        if page >= 0:  # Page 0 is often the default or first page
            query_parts.append(str(page))
        if period:
            query_parts.append(period)

        query_string = ":".join(query_parts)
        params = {"q": query_string}

        raw_data = await self._request("GET", "/q.php", params=params)
        if not isinstance(raw_data, list):
            if isinstance(raw_data, dict) and raw_data.get("error"):
                raise TPBContentError(f"API returned an error: {raw_data.get('error')}")
            if isinstance(raw_data, dict) and not raw_data:
                return []
            raise TPBContentError(f"Unexpected API response format for by_user. Expected list, got {type(raw_data)}")
        return parse_torrent_list(raw_data)

    async def file_list(self, torrent_id: int) -> List[FileEntry]:
        """
        Get the list of files for a specific torrent.

        Args:
            torrent_id (int): The ID of the torrent.

        Returns:
            List[FileEntry]: A list of files in the torrent.
        """
        params = {"id": torrent_id}
        raw_data = await self._request("GET", "/f.php", params=params)
        if not isinstance(raw_data, list):
            # API might return empty string for non-existent torrent or torrent with no file list
            if raw_data == {} or raw_data == []:  # Handled by _request or means empty list.
                return []
            raise TPBContentError(f"Unexpected API response format for file_list. Expected list, got {type(raw_data)}")
        return parse_file_list(raw_data)

    async def get_user_page_count(self, username: str) -> int:
        """
        Get the number of pages of torrents for a given user.
        The API returns a single-element list with a number as a string.

        Args:
            username (str): The username.

        Returns:
            int: The number of pages. Returns 0 if user not found or error.
        """
        params = {"q": f"pcnt:{username}"}
        raw_data = await self._request("GET", "/q.php", params=params)
        try:
            if isinstance(raw_data, list) and len(raw_data) == 1:
                # The API returns a list with a single string number: ["15"]
                return int(raw_data[0])
            return 0  # Or raise error
        except (ValueError, TypeError, IndexError):
            return 0  # Or raise error

    def set_base_url(self, url: str):
        """
        Change the base URL for the API.
        This will close the current internal client and create a new one if it was managed internally.
        If an external client was provided, its base_url is not changed by this method.

        Args:
            url (str): The new base URL.
        """
        if self._external_client:
            # Cannot change base_url of an externally provided client this way
            # User should re-initialize AsyncTPBClient with a new client or new base_url
            # Or, the external client's base_url needs to be updated externally.
            # For now, we'll just update our internal record.
            self.base_url = url.rstrip('/')
            print(
                "Warning: Base URL of an externally provided client cannot be changed by set_base_url. Update the client externally or re-initialize AsyncTPBClient.")
            return

        # Close old client and create a new one
        # This is not ideal in async context without `await self.close()`
        # Better to advise re-instantiation or provide an async method for this.
        # For simplicity now, we'll just re-assign. User should ideally close old one.
        self.base_url = url.rstrip('/')
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        # Note: This creates a new client but doesn't implicitly close the old one.
        # Proper async resource management would require `await self.close()` first.
        # A better pattern is to re-instantiate the AsyncTPBClient.
        self._client = httpx.AsyncClient(base_url=self.base_url, headers=headers, follow_redirects=True)

    async def close(self):
        """
        Closes the underlying httpx client if it was created internally.
        """
        if not self._external_client and hasattr(self, '_client') and self._client is not None:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
