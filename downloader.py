from pathlib import Path
import yt_dlp

class SoundVaultDownloader:
    def __init__(self, download_dir: str = "downloads"):
        # "C:\Filipps Fotos-Videos"
        self.base_dir = Path(__file__).resolve().parent
        self.download_directory = self.base_dir / download_dir
        self.archive_file = self.base_dir / 'archive.txt'
        self.download_directory.mkdir(parents=True, exist_ok=True)

    def _progress_hook(self, d: dict) -> None:
        if d['status'] == 'downloading':
            filename = Path(d.get('filename', '')).name
            percent = d.get('_percent_str', '0.0%').strip()
            speed = d.get('_speed_str', 'N/A').strip()
            eta = d.get('_eta_str', 'N/A').strip()

            print(f"\r[Downloading] {percent} of {filename} ({speed}, ETA: {eta})", end="", flush=True)

        elif d['status'] == 'finished':
            filename = Path(d.get('filename', '')).name
            print(f"\n[Finished] {filename} -> Processing audio & metadata...")

    def download(self, playlist_url: str) -> None:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': {'default': str(self.download_directory / '%(playlist_title,downloads)s' / '%(title)s.%(ext)s')},
            'ignoreerrors': True,
            'download_archive': str(self.archive_file),
            'js_runtimes': {'node': {}},
            'quiet': True,
            'noprogress': True,
            'progress_hooks': [self._progress_hook],


            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '0',
                },
                {'key': 'FFmpegMetadata'},
                {'key': 'EmbedThumbnail'},
            ],
            'writethumbnail': True,
            'clean_infojson': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([playlist_url])