# just-tbp/examples/search.py

import asyncio  # For async example if we add one later, for now just for structure
from just_tbp import (
    TPBClient,
    TPBRequestError,
    TPBContentError,
    CATEGORIES,
    VIDEO_HD_MOVIES,  # Example specific category constant
    Torrent,
    TorrentDetails
)


def print_torrent_summary(torrent: Torrent):
    """Helper function to print torrent summary."""
    print(f"  ID: {torrent.id}, Name: {torrent.name}")
    print(f"    Seeders: {torrent.seeders}, Leechers: {torrent.leechers}, Size: {torrent.size // (1024 * 1024)} MB")
    print(f"    Uploaded by: {torrent.username} on {torrent.added.strftime('%Y-%m-%d')}")
    print(f"    Category ID: {torrent.category}, Status: {torrent.status}")
    if torrent.imdb:
        print(f"    IMDb: {torrent.imdb}")
    print("-" * 20)


def print_torrent_details_summary(details: TorrentDetails):
    """Helper function to print torrent details."""
    print(f"Torrent Details for ID: {details.id}")
    print(f"  Name: {details.name}")
    print(f"  Info Hash: {details.info_hash}")
    print(f"  Seeders: {details.seeders}, Leechers: {details.leechers}")
    print(f"  Size: {details.size // (1024 * 1024)} MB, Num Files: {details.num_files}")
    print(f"  Uploaded by: {details.username} on {details.added.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Status: {details.status}, Category ID: {details.category}")
    if details.imdb:
        print(f"  IMDb: {details.imdb}")
    if details.language:
        print(f"  Language: {details.language}")
    if details.text_language:
        print(f"  Text Language: {details.text_language}")
    print(f"  Description:\n{details.descr[:200]}...")  # Print first 200 chars of description
    print("=" * 30)


def main():
    # Using the client as a context manager ensures it's closed properly
    with TPBClient() as client:
        try:
            # --- Example 1: Basic Search ---
            print(">>> Example 1: Searching for 'Black Mirror'...")
            search_query = "Black Mirror"
            results = client.search(search_query)

            if results:
                print(f"Found {len(results)} torrents for '{search_query}':")
                for torrent in results[:3]:  # Print first 3 results
                    print_torrent_summary(torrent)

                # --- Example 2: Get Details for the first torrent ---
                if results[0].id:
                    first_torrent_id = results[0].id
                    print(f"\n>>> Example 2: Getting details for torrent ID: {first_torrent_id}...")
                    details = client.details(first_torrent_id)
                    if details:
                        print_torrent_details_summary(details)
                    else:
                        print(f"Could not retrieve details for torrent ID: {first_torrent_id}")
            else:
                print(f"No results found for '{search_query}'.")

            # --- Example 3: Search with a specific category ---
            # You can use CATEGORIES dictionary or the direct constant
            hd_movies_cat_id = CATEGORIES["video"]["hd_movies"]
            # Or directly: from just_tbp import VIDEO_HD_MOVIES
            # hd_movies_cat_id = VIDEO_HD_MOVIES

            print(f"\n>>> Example 3: Searching for 'action movie' in HD Movies (ID: {hd_movies_cat_id})...")
            action_results = client.search("action movie", category_id=hd_movies_cat_id)
            if action_results:
                print(f"Found {len(action_results)} action movies in HD:")
                for torrent in action_results[:2]:  # Print first 2 results
                    print_torrent_summary(torrent)
            else:
                print("No action movies found in HD category for that query.")

            # --- Example 4: Get Top 100 recent torrents ---
            print("\n>>> Example 4: Getting Top 100 recent torrents...")
            recent_torrents = client.recent()  # or client.top100("recent")
            if recent_torrents:
                print(f"Found {len(recent_torrents)} recent torrents (showing first 3):")
                for torrent in recent_torrents[:3]:
                    print_torrent_summary(torrent)
            else:
                print("Could not retrieve recent torrents.")

            # --- Example 5: Get Top 100 HD Movies ---
            print(f"\n>>> Example 5: Getting Top 100 HD Movies (ID: {VIDEO_HD_MOVIES})...")
            top_hd_movies = client.top100(VIDEO_HD_MOVIES)
            if top_hd_movies:
                print(f"Found {len(top_hd_movies)} top HD movies (showing first 3):")
                for torrent in top_hd_movies[:3]:
                    print_torrent_summary(torrent)
            else:
                print(f"Could not retrieve top HD Movies.")

            # --- Example 6: Search by username ---
            # Note: Usernames can be tricky and might not always yield results
            # if the user doesn't exist or has no public uploads via this API.
            test_username = "YTSAGx"  # A known uploader, replace if needed
            print(f"\n>>> Example 6: Searching for torrents by user '{test_username}'...")
            user_torrents = client.by_user(test_username)
            if user_torrents:
                print(f"Found {len(user_torrents)} torrents by user '{test_username}' (showing first 3):")
                for torrent in user_torrents[:3]:
                    print_torrent_summary(torrent)
            else:
                print(f"No torrents found for user '{test_username}' or user does not exist.")

            # --- Example 7: Searching for non-existent torrent details ---
            print("\n>>> Example 7: Attempting to get details for a non-existent torrent ID (999999999)...")
            non_existent_details = client.details(999999999)
            if non_existent_details:
                print("This should not happen. Found details for a non-existent ID.")
            else:
                print("Correctly received no details for non-existent torrent ID.")

                # --- Example 1: Basic Search ---
                print(">>> Example 1: Searching for 'ubuntu'...")
                search_query = "ubuntu"
                results = client.search(search_query)

                if results:
                    print(f"Found {len(results)} torrents for '{search_query}':")
                    for torrent in results[:3]:  # Print first 3 results
                        print_torrent_summary(torrent)

                    # --- Example 2: Get Details for the first torrent ---
                    if results[0].id:
                        first_torrent_id = results[0].id
                        print(f"\n>>> Example 2: Getting details for torrent ID: {first_torrent_id}...")
                        details = client.details(first_torrent_id)
                        if details:
                            print_torrent_details_summary(details)
                        else:
                            print(f"Could not retrieve details for torrent ID: {first_torrent_id}")
                else:
                    print(f"No results found for '{search_query}'.")


        except TPBRequestError as e:
            print(f"\nAn API request error occurred: {e}")
        except TPBContentError as e:
            print(f"\nAn API content error occurred: {e}")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
    # If you weren't using the client with a context manager:
    # client = TPBClient()
    # try:
    #    # ... your code ...
    # finally:
    #    client.close()
    # But the 'with' statement is preferred.
