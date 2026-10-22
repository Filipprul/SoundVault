from src.downloader import SoundVaultDownloader


def test_download_pipeline():
    downloader = SoundVaultDownloader()

    test_url = "https://youtu.be/GPNbnromGgk?si=41veKfiJOViuVUOV"

    print("Starte Test-Download und Metadaten-Pipeline...")
    downloader.download(test_url)
    print("Test abgeschlossen! Prüfe den Download-Ordner und die ID3-Tags.")

if __name__ == "__main__":
    test_download_pipeline()