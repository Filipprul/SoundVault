import json
import socket
from pathlib import Path
import yt_dlp

class SoundVaultLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        if "getaddrinfo failed" in msg or "TransportError" in msg or "Name or service not known" in msg:
            raise ConnectionError("Internetverbindung während des Vorgangs verloren!")

class SoundVaultDownloader:
    def __init__(self, config_file: str = "config.json"):
        self.base_dir = Path(__file__).resolve().parent
        self.config_path = self.base_dir / config_file
        self.config = self._load_config()

        self.download_directory = self.base_dir / self.config.get("download_dir", "downloads")
        self.archive_file = self.base_dir / 'archive.txt'
        self.download_directory.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> dict:
        default_config = {
            "download_dir": "downloads",
            "audio_format": "mp3",
            "audio_quality": "0"
        }

        if not self.config_path.exists():
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            return default_config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default_config

    @staticmethod
    def check_network() -> bool:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def _progress_hook(self, d: dict) -> None:
        if not self.check_network():
            raise ConnectionError("Internetverbindung während des Downloads verloren!")

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
        if not self.check_network():
            raise ConnectionError("No active internet connection. Please check your network and try again.")

        audio_format = self.config.get("audio_format", "mp3")
        audio_quality = self.config.get("audio_quality", "0")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': {'default': str(self.download_directory / '%(playlist_title,downloads)s' / '%(title)s.%(ext)s')},
            'ignoreerrors': True,
            'no_warnings': True,
            'download_archive': str(self.archive_file),
            'js_runtimes': {'node': {}},
            'logger': SoundVaultLogger(),
            'retries': 1,
            'fragment_retries': 1,
            'socket_timeout': 3,
            'quiet': True,
            'noprogress': True,
            'progress_hooks': [self._progress_hook],

            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format,
                    'preferredquality': audio_quality,
                },
                {'key': 'FFmpegMetadata'},
                {'key': 'EmbedThumbnail'},
            ],
            'writethumbnail': True,
            'clean_infojson': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([playlist_url])
        except ConnectionError as ce:
            raise ce
        except Exception as e:
            if not self.check_network():
                raise ConnectionError("Internetverbindung unterbrochen.")
            raise RuntimeError(f"Download-Fehler: {e}")