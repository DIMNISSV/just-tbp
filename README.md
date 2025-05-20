# Just TPB

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/) 

`just-tbp` is a simple, modern, and asynchronous Python client for interacting with The Pirate Bay API, primarily targeting the `apibay.org` endpoint by default. It provides an easy-to-use interface to search for torrents, get torrent details, fetch top torrents, retrieve file lists, and more.

This library is a Python port and reimagining of the TypeScript library [apibay-master](https://github.com/ χαρακτηρισμός/apibay-master) (assuming this was the origin, adjust if not), significantly enhanced with asynchronous capabilities and more comprehensive API coverage.

## Features

*   Asynchronous operations using `httpx`.
*   Search for torrents by query, category, and user-defined pagination.
*   Retrieve detailed information about specific torrents.
*   Fetch file lists for torrents.
*   Fetch top 100 torrents for various categories, including "all" and "recent" (with potential pagination for recent).
*   List torrents uploaded by a specific user, with pagination and period filters (e.g., "today").
*   Get the approximate page count for a user's torrents.
*   Typed for better autocompletion and static analysis (with MyPy).
*   Sensible error handling with custom exceptions.
*   Utilities for generating magnet links and formatting data (size, datetime).
*   Includes an auto-generation script for API category constants based on TPB's JavaScript.

## Installation

Since this package is not intended for PyPI, you can install it directly from its Git repository or by cloning it locally.

**Using pip with Git:**

```bash
pip install git+https://github.com/dimnissv/just-tbp.git
```

**Or, clone and install locally (recommended for development):**

1.  Clone the repository:
    ```bash
    git clone https://github.com/dimnissv/just-tbp.git
    cd just-tbp
    ```
2.  Install using Poetry (manages dependencies and virtual environments):
    ```bash
    poetry install
    ```
    This will also install development dependencies.
3.  Activate the virtual environment:
    ```bash
    poetry shell
    ```

## Quick Start

Here's a quick example demonstrating asynchronous usage:

```python
import asyncio
from just_tbp import (
    AsyncTPBClient,
    TPBRequestError,
    TPBContentError,
    generate_magnet_link,
    format_size
)
# Assuming your constants are generated and accessible, e.g., from just_tbp.constants import VIDEO_HD_MOVIES
# For this example, we'll use the CATEGORIES dictionary if constants_generated is used
# or a hardcoded ID if you haven't run the generation script yet.
try:
    from just_tbp.constants import CATEGORIES
    VIDEO_HD_MOVIES = CATEGORIES.get("video", {}).get("hd_movies", 207) # Example
except ImportError:
    VIDEO_HD_MOVIES = 207

async def run_examples():
    # Using the client as an async context manager is recommended
    async with AsyncTPBClient() as client:
        try:
            # Search for 'ubuntu' torrents
            print("Searching for 'ubuntu'...")
            results = await client.search("ubuntu")
            if results:
                print(f"Found {len(results)} torrents for 'ubuntu'. First result:")
                first_torrent = results[0]
                print(f"  ID: {first_torrent.id}, Name: {first_torrent.name}")
                print(f"  Seeders: {first_torrent.seeders}, Leechers: {first_torrent.leechers}")
                print(f"  Size: {format_size(first_torrent.size)}")
                print(f"  Magnet: {generate_magnet_link(first_torrent.info_hash, first_torrent.name)}")

                # Get details for the first torrent
                print(f"\nGetting details for torrent ID: {first_torrent.id}...")
                details = await client.details(first_torrent.id)
                if details:
                    print(f"  Description (partial): {details.descr[:100]}...")

                # Get file list for the first torrent
                print(f"\nGetting file list for torrent ID: {first_torrent.id}...")
                files = await client.file_list(first_torrent.id)
                if files:
                    print("  Files:")
                    for f_entry in files[:3]: # Show first 3 files
                        print(f"    - {f_entry.name} ({format_size(f_entry.size)})")
            else:
                print("No results found for 'ubuntu'.")

            # Get top 100 HD Movies
            print(f"\nFetching top 100 HD Movies (Category ID: {VIDEO_HD_MOVIES})...")
            top_movies = await client.top100(VIDEO_HD_MOVIES)
            if top_movies:
                print(f"Found {len(top_movies)} top HD movies. First one: {top_movies[0].name}")

        except TPBRequestError as e:
            print(f"An API request error occurred: {e}")
        except TPBContentError as e:
            print(f"An API content error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(run_examples())
```
You can find more comprehensive examples in the `examples/async_search.py` file.

## API Overview

The main entry point is the `AsyncTPBClient` class. All API-calling methods are asynchronous and need to be `await`ed.

*   `async client.search(query: str, category_id: Optional[CategoryId] = None, page: int = 0) -> List[Torrent]`
*   `async client.details(torrent_id: int) -> Optional[TorrentDetails]`
*   `async client.file_list(torrent_id: int) -> List[FileEntry]`
*   `async client.top100(category: Top100Category, page: Optional[int] = None) -> List[Torrent]`
*   `async client.recent(page: Optional[int] = None) -> List[Torrent]`
*   `async client.by_user(username: str, page: int = 0, period: Optional[str] = None) -> List[Torrent]`
    *   `period` can be "today", "twodays", "threedays" (API support dependent).
*   `async client.get_user_page_count(username: str) -> int`
*   `client.set_base_url(url: str)` (Synchronous method to change config)
*   `async client.close()` (Automatically called if using `async with`)

Refer to `examples/async_search.py` for practical usage.

### Categories

Category IDs are crucial for filtering searches and fetching top lists. `just-tbp` provides these primarily through a generated constants file (`just_tbp/constants_generated.py` or `just_tbp/constants.py` if you rename/merge).

**1. `CATEGORIES` Dictionary:**
A nested dictionary `just_tbp.CATEGORIES` maps category names to their numerical IDs.
```python
from just_tbp import CATEGORIES # Ensure constants are generated and imported

# Example access (keys depend on generated constants)
hd_movies_id = CATEGORIES.get("video", {}).get("hd_movies") # e.g., 207
music_id = CATEGORIES.get("audio", {}).get("music")         # e.g., 101
```

**2. Direct Category Constants:**
The generation script also creates individual constants like `AUDIO_MUSIC`, `VIDEO_HD_MOVIES`, etc.
```python
from just_tbp.constants_generated import VIDEO_HD_MOVIES, AUDIO_MUSIC # Adjust import if needed

print(f"HD Movies ID: {VIDEO_HD_MOVIES}")
```
To generate/update these constants, run the script:
```bash
python scripts/generate_categories.py
```
Review the output (`just_tbp/constants_generated.py`) and merge/rename it to `just_tbp/constants.py` as needed.

### Data Models

The library uses `dataclasses` for representing API responses:
*   `Torrent`: For items in search results and top lists.
    ```python
    @dataclass
    class Torrent:
        id: int
        name: str
        info_hash: str
        leechers: int
        seeders: int
        num_files: int
        size: int # Bytes
        username: str
        added: datetime # UTC aware
        status: str
        category: CategoryId
        imdb: Optional[str] = None
    ```
*   `TorrentDetails`: For detailed information about a single torrent.
    ```python
    @dataclass
    class TorrentDetails:
        # ... (all fields from Torrent)
        descr: str
        language: Optional[str] = None
        text_language: Optional[str] = None
    ```
*   `FileEntry`: For files within a torrent.
    ```python
    @dataclass
    class FileEntry:
        name: str
        size: int # Bytes
    ```

### Utility Functions

`just_tbp.utils` provides helpful functions:
*   `generate_magnet_link(info_hash: str, name: str, trackers: Optional[Sequence[str]] = None) -> str`
*   `format_size(size_bytes: int) -> str` (e.g., "1.23 GiB")
*   `format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S %Z") -> str`

### Error Handling

The library defines custom exceptions:
*   `TPBRequestError`: For issues related to the HTTP request itself (network errors, HTTP 4xx/5xx errors).
*   `TPBContentError`: For issues with the content received from the API (e.g., malformed JSON, unexpected data structure).

Example:
```python
try:
    async with AsyncTPBClient() as client:
        results = await client.search("some query")
except TPBRequestError as e:
    print(f"Request Error: {e}")
except TPBContentError as e:
    print(f"Content Error: {e}")
```

### Advanced Configuration

*   **Custom Base URL:**
    ```python
    client = AsyncTPBClient(base_url="https://your-apibay-mirror.com")
    # or after initialization:
    # client.set_base_url("https://your-apibay-mirror.com")
    ```
*   **External `httpx.AsyncClient`:** You can pass your own pre-configured `httpx.AsyncClient` instance.
    ```python
    import httpx
    my_custom_client = httpx.AsyncClient(timeout=30.0, headers={"X-My-Header": "value"})
    tpb_client = AsyncTPBClient(client=my_custom_client, base_url="https://apibay.org") 
    # Make sure base_url matches what the client expects or is set on the client
    # ...
    await my_custom_client.aclose() # You are responsible for closing it
    ```

## Development

This project uses [Poetry](https://python-poetry.org/) for dependency management and packaging.

1.  **Setup:**
    ```bash
    git clone https://github.com/dimnissv/just-tbp.git
    cd just-tbp
    poetry install 
    poetry shell
    ```
2.  **Generating Category Constants:**
    The API category IDs and names can change. A script is provided to attempt to regenerate them from TPB's `main.js`.
    ```bash
    python scripts/generate_categories.py
    ```
    This will create `just_tbp/constants_generated.py`. Review this file carefully and then replace or merge its content into `just_tbp/constants.py`.
3.  **Linting & Formatting:**
    [Ruff](https://beta.ruff.rs/docs/) is used for linting and formatting.
    ```bash
    poetry run ruff check . --fix
    poetry run ruff format .
    ```
4.  **Running Examples:**
    ```bash
    poetry run python examples/async_search.py
    ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue for bugs, feature requests, or improvements.

## Disclaimer

This library is intended for educational purposes and for interacting with publicly available APIs. The developers of this library do not endorse or encourage copyright infringement or any illegal activity. Please respect the laws in your country and the terms of service of any API you interact with. Accessing and using torrent-related services may carry risks; use at your own discretion and responsibility.

## Donate

You can support the development of this project via Monero:

`87QGCoHeYz74Ez22geY1QHerZqbN5J2z7JLNgyWijmrpCtDuw66kR7UQsWXWd6QCr3G86TBADcyFX5pNaqt7dpsEHE9HBJs`

[![imageban](https://i4.imageban.ru/thumbs/2025.04.15/566393a122f2a27b80defcbe9b074dc0.png)](https://imageban.ru/show/2025/04/15/566393a122f2a27b80defcbe9b074dc0/png)

I will also be happy to arrange any other way for you to transfer funds, please contact me.

## Contacts

*   Telegram: [@dimnissv](https://t.me/dimnissv)
*   Email: [dimnissv@yandex.kz](mailto:dimnissv@yandex.kz)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
