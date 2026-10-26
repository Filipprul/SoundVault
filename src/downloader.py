import json
import socket
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yt_dlp

from src.utils.metadata_handler import apply_id3_tags, fetch_metadata_from_musicbrainz
from src.utils.title_cleaner import clean_title


class SoundVaultLogger:
    def __init__(self, status_callback: Callable[[str], None] | None = None) -> None:
        self.status_callback = status_callback

    def debug(self, msg: str) -> None:
        pass

    def warning(self, msg: str) -> None:
        pass

    def error(self, msg: str) -> None:
        if (
            "getaddrinfo failed" in msg
            or "TransportError" in msg
            or "Name or service not known" in msg
        ):
            err_msg = "Internetverbindung während des Vorgangs verloren!"
            if self.status_callback:
                self.status_callback(err_msg)
            raise ConnectionError(err_msg)


class SoundVaultDownloader:
    def __init__(
        self,
        config_file: str = "config.json",
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
        status_callback: Callable[[str], None] | None = None,
    ) -> None:
        self.base_dir = Path(__file__).resolve().parent.parent
        self.config_path = self.base_dir / config_file
        self.config = self._load_config()

        self.progress_callback = progress_callback
        self.status_callback = status_callback

        self.download_directory = self.base_dir / self.config.get(
            "download_dir", "downloads"
        )
        self.download_directory.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> dict[str, Any]:
        default_config: dict[str, Any] = {
            "download_dir": "downloads",
            "audio_format": "mp3",
            "audio_quality": "0",
        }

        if not self.config_path.exists():
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
            return default_config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default_config

    @staticmethod
    def check_network() -> bool:
        try:
            with socket.create_connection(("8.8.8.8", 53), timeout=3):
                return True
        except OSError:
            return False

    def _progress_hook(self, d: dict[str, Any]) -> None:
        if not self.check_network():
            msg = "Internetverbindung während des Downloads verloren!"
            if self.status_callback:
                self.status_callback(msg)
            raise ConnectionError(msg)

        if self.progress_callback:
            self.progress_callback(d)

        if d["status"] == "downloading":
            filename = Path(d.get("filename", "")).name
            percent = d.get("_percent_str", "0.0%").strip()
            speed = d.get("_speed_str", "N/A").strip()
            eta = d.get("_eta_str", "N/A").strip()

            print(
                f"\r[Downloading] {percent} of {filename} ({speed}, ETA: {eta})",
                end="",
                flush=True,
            )

        elif d["status"] == "finished":
            filename = Path(d.get("filename", "")).name
            msg = f"\n[Finished] {filename} -> Downloading stream complete."
            if self.status_callback:
                self.status_callback(msg)
            else:
                print(msg)

    def _postprocessor_hook(self, d: dict[str, Any]) -> None:
        if (
            d["status"] == "finished"
            and d.get("postprocessor_name") == "FFmpegExtractAudio"
        ):
            msg = "\n[Postprocessor] Audio extracted, applying metadata & tags..."
            if self.status_callback:
                self.status_callback(msg)
            else:
                print(msg)

            audio_format = self.config.get("audio_format", "mp3")
            file_path = Path(d.get("info_dict", {}).get("filepath", "")).with_suffix(
                f".{audio_format}"
            )

            if file_path.exists():
                info_dict = d.get("info_dict", {})
                raw_title = info_dict.get("title", file_path.stem)

                cleaned_title = clean_title(raw_title)

                metadata = fetch_metadata_from_musicbrainz(cleaned_title)
                if metadata:
                    apply_id3_tags(str(file_path), metadata)
                    safe_artist = "".join(
                        c
                        for c in metadata.get("artist", "Unknown")
                        if c.isalnum() or c in (" ", "-", "_")
                    ).strip()
                    safe_title = "".join(
                        c
                        for c in metadata.get("title", cleaned_title)
                        if c.isalnum() or c in (" ", "-", "_")
                    ).strip()

                    new_filename = f"{safe_artist} - {safe_title}.{audio_format}"
                    new_path = file_path.parent / new_filename

                    try:
                        if file_path != new_path:
                            if new_path.exists():
                                counter = 1
                                while new_path.exists():
                                    new_path = file_path.parent / f"{safe_artist} - {safe_title}_{counter}.{audio_format}"
                                    counter += 1
                            file_path.rename(new_path)
                            print(f"[Metadata] Successfully renamed to: {new_path.name}")
                    except Exception as e:
                        print(f"[Metadata] Renaming error: {e}")

    def download(self, playlist_url: str) -> None:
        if not self.check_network():
            raise ConnectionError(
                "No active internet connection. Please check your network and try again."
            )

        audio_format = self.config.get("audio_format", "mp3")
        audio_quality = self.config.get("audio_quality", "0")

        ydl_opts: dict[str, Any] = {
            "format": "bestaudio/best",
            "outtmpl": {
                "default": str(
                    self.download_directory
                    / "%(playlist_title,downloads)s"
                    / "%(title)s.%(ext)s"
                )
            },
            "ignoreerrors": True,
            "no_warnings": True,
            "js_runtimes": {"node": {}},
            "logger": SoundVaultLogger(status_callback=self.status_callback),
            "retries": 1,
            "fragment_retries": 1,
            "socket_timeout": 3,
            "quiet": True,
            "noprogress": True,
            "progress_hooks": [self._progress_hook],
            "postprocessor_hooks": [self._postprocessor_hook],
            "writethumbnail": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format,
                    "preferredquality": audio_quality,
                },
                {"key": "FFmpegThumbnailsConvertor", "format": "jpg"},
                {"key": "FFmpegMetadata", "add_metadata": True},
                {"key": "EmbedThumbnail", "already_have_thumbnail": False},
            ],
            "clean_infojson": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([playlist_url])
        except ConnectionError:
            raise
        except Exception as e:
            if not self.check_network():
                raise ConnectionError("Internetverbindung unterbrochen.")
            raise RuntimeError(f"Download-Fehler: {e}")
