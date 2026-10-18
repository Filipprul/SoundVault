import sys
from downloader import SoundVaultDownloader

def get_valid_url() -> str:
    while True:
        url = input("\nEnter YouTube Playlist or Video URL (or 'q' to quit): ").strip()

        if url.lower() in ['q', 'quit', 'exit']:
            print("Operation canceled by user.")
            sys.exit(0)

        if not url:
            print("Error: Input cannot be empty. Please try again.")
            continue

        if not (url.startswith("http://") or url.startswith("https://")):
            print("Error: Please enter a valid URL starting with http:// or https://")
            continue

        return url

def main():
    print("=== SoundVault Audio Downloader ===")

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

if __name__ == '__main__':
    main()