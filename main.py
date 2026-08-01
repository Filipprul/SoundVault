from downloader import SoundVaultDownloader

def main():
    print("=== SoundVault Audio Downloader ===")

    url = input("\nEnter Youtube Playlist or Video URL: ").strip()

    if not url:
        print("Error: No URL provided. Exiting...")
        return

    print("\nStarting download process...")

    downloader = SoundVaultDownloader()
    downloader.download(url)

    print("\nProcess completed successfully!")


if __name__ == '__main__':
    main()