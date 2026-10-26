import json
import sys
from pathlib import Path
from typing import Any

from src.downloader import SoundVaultDownloader
from src.watchdog import PlaylistWatchdog


def load_config() -> dict[str, Any]:
    config_path = Path("config.json")
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: S110
            pass
    return {
        "monitored_playlists": [],
        "watchdog_interval_seconds": 1800,
    }


def get_valid_url() -> str:
    while True:
        url = input("\nEnter YouTube Playlist or Video URL (or 'q' to quit): ").strip()

        if url.lower() in ["q", "quit", "exit"]:
            print("Operation canceled by user.")
            sys.exit(0)

        if not url:
            print("Error: Input cannot be empty. Please try again.")
            continue

        if not url.startswith(("http://", "https://")):
            print("Error: Please enter a valid URL starting with http:// or https://")
            continue

        return url


def main() -> None:
    print("=== SoundVault Audio Downloader ===")

    config = load_config()
    playlists = config.get("monitored_playlists", [])
    interval = config.get("watchdog_interval_seconds", 1800)

    watchdog = PlaylistWatchdog(playlist_urls=playlists, interval_seconds=interval)
    watchdog.start()

    try:
        url = get_valid_url()
        print("\nStarting download process...")

        downloader = SoundVaultDownloader()
        downloader.download(url)

        print("\nProcess completed successfully!")

    except ConnectionError as ce:
        print(f"\n[Network Error] {ce}")
    except RuntimeError as re:
        print(f"\n[Download Failed] {re}")
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user. Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
