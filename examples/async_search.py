# examples/async_search.py
import asyncio
from just_tbp import (
    AsyncTPBClient,
    TPBRequestError,
    TPBContentError,
    CATEGORIES,  # Will come from generated constants
    # VIDEO_HD_MOVIES, # Example if you export individual constants
    Torrent,
    TorrentDetails,
    FileEntry,
    generate_magnet_link,
    format_size,
    format_datetime
)

# Try to get a specific category ID for example, fallback if not found
try:
    # This assumes your generated constants will have these specific names
    # Or you access them via CATEGORIES dict: CATEGORIES["video"]["hd_movies"]
    from just_tbp.constants_generated import VIDEO_HD_MOVIES  # Adjust path if needed
except ImportError:
    VIDEO_HD_MOVIES = 207  # Fallback


def print_torrent_summary(torrent: Torrent):
    print(f"  ID: {torrent.id}, Name: {torrent.name}")
    print(f"    Seeders: {torrent.seeders}, Leechers: {torrent.leechers}, Size: {format_size(torrent.size)}")
    print(f"    Uploaded by: {torrent.username} on {format_datetime(torrent.added, '%Y-%m-%d')}")
    print(f"    Category ID: {torrent.category}, Status: {torrent.status}")
    print(f"    Magnet: {generate_magnet_link(torrent.info_hash, torrent.name)}")
    if torrent.imdb:
        print(f"    IMDb: {torrent.imdb}")
    print("-" * 20)


def print_torrent_details_summary(details: TorrentDetails):
    print(f"Torrent Details for ID: {details.id}")
    print(f"  Name: {details.name}")
    print(f"  Info Hash: {details.info_hash}")
    print(f"  Magnet: {generate_magnet_link(details.info_hash, details.name)}")
    # ... (other details as before, using format_size and format_datetime) ...
    print(f"  Description:\n{details.descr[:200]}...")
    print("=" * 30)


def print_file_list(files: list[FileEntry]):
    if not files:
        print("  No files listed for this torrent.")
        return
    print("  Files:")
    for file_entry in files:
        print(f"    - {file_entry.name} ({format_size(file_entry.size)})")
    print("-" * 20)


async def main():
    async with AsyncTPBClient() as client:  # Use async context manager
        try:
            # --- Example 1: Basic Search ---
            print(">>> Example 1: Searching for 'ubuntu'...")
            search_query = "ubuntu"
            results = await client.search(search_query)  # await

            if results:
                print(f"Found {len(results)} torrents for '{search_query}':")
                for torrent in results[:2]:  # Print first 2 results
                    print_torrent_summary(torrent)

                first_torrent_id = results[0].id
                # --- Example 2: Get Details for the first torrent ---
                print(f"\n>>> Example 2: Getting details for torrent ID: {first_torrent_id}...")
                details = await client.details(first_torrent_id)  # await
                if details:
                    print_torrent_details_summary(details)
                else:
                    print(f"Could not retrieve details for torrent ID: {first_torrent_id}")

                # --- Example 2b: Get File List for the first torrent ---
                print(f"\n>>> Example 2b: Getting file list for torrent ID: {first_torrent_id}...")
                files = await client.file_list(first_torrent_id)  # await
                print_file_list(files)

            else:
                print(f"No results found for '{search_query}'.")

            # --- Example 3: Search by username and get page count ---
            test_username = "YTSAGx"  # A known uploader, or one from parsed CATEGORIES
            print(f"\n>>> Example 3: User '{test_username}'...")
            page_count = await client.get_user_page_count(test_username)
            print(f"User '{test_username}' has ~{page_count} pages of torrents.")

            if page_count > 0:
                print(f"Fetching first page of torrents for user '{test_username}'...")
                user_torrents_page0 = await client.by_user(test_username, page=0)
                if user_torrents_page0:
                    print(
                        f"Found {len(user_torrents_page0)} torrents by '{test_username}' on page 0 (showing first 1):")
                    print_torrent_summary(user_torrents_page0[0])

                # Example: Fetching with period filter (if API supports it well)
                # user_torrents_today = await client.by_user(test_username, period="today")
                # if user_torrents_today:
                # print(f"Found {len(user_torrents_today)} torrents by '{test_username}' for 'today'.")

            # --- Example 4: Top 100 Recent (paginated example if API supports) ---
            print("\n>>> Example 4: Getting Top 100 recent torrents (page 0)...")
            recent_torrents_p0 = await client.recent(page=0)
            if recent_torrents_p0:
                print(f"Found {len(recent_torrents_p0)} recent torrents on page 0 (showing first 1):")
                print_torrent_summary(recent_torrents_p0[0])

            # Some APIs might have data_top100_recent_1.json etc.
            # print("\nGetting Top 100 recent torrents (page 1)...")
            # recent_torrents_p1 = await client.recent(page=1)
            # if recent_torrents_p1:
            #     print(f"Found {len(recent_torrents_p1)} recent torrents on page 1.")
            # else:
            #     print("No recent torrents found on page 1 (or API doesn't support this pagination).")


        except TPBRequestError as e:
            print(f"\nAn API request error occurred: {e}")
        except TPBContentError as e:
            print(f"\nAn API content error occurred: {e}")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}", type(e))


if __name__ == "__main__":
    asyncio.run(main())
