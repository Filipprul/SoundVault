import logging
import threading

import yt_dlp

from src.downloader import SoundVaultDownloader
from src.utils.archive import is_downloaded, mark_as_downloaded

logger = logging.getLogger(__name__)


class PlaylistWatchdog:
    def __init__(
        self,
        playlist_urls: list,
        interval_seconds: int = 1800,
        status_callback=None,
    ):
        self.playlist_urls = [
            url for url in playlist_urls if url and "Insert playlist-url" not in url
        ]
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self.downloader = SoundVaultDownloader()
        self.status_callback = status_callback

    def _notify(self, message: str):
        logger.info(message)
        if self.status_callback:
            try:
                self.status_callback(message)
            except Exception: # noqa: S110
                pass

    def start(self):
        if not self.playlist_urls:
            return

        thread = threading.Thread(target=self._run_loop, daemon=True)
        thread.start()
        self._notify("Playlist Watchdog started in background.")

    def _run_loop(self):
        while not self._stop_event.is_set():
            for url in self.playlist_urls:
                if self._stop_event.is_set():
                    break
                try:
                    self._notify(f"Checking playlist: {url}")
                    ydl_opts = {
                        "extract_flat": True,
                        "skip_download": True,
                        "quiet": True,
                        "no_warnings": True,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        if info and "entries" in info:
                            for entry in info["entries"]:
                                if not entry:
                                    continue
                                video_id = entry.get("id")
                                title = entry.get("title", "Unknown Title")
                                if video_id and not is_downloaded(video_id):
                                    self._notify(
                                        f"New track found: {title}. Downloading..."
                                    )
                                    track_url = (
                                        entry.get("url")
                                        or f"https://www.youtube.com/watch?v={video_id}"
                                    )
                                    try:
                                        self.downloader.download(track_url)
                                        mark_as_downloaded(video_id, title)
                                        self._notify(f"Downloaded: {title}")
                                    except Exception as dl_err:
                                        logger.error(
                                            f"Failed to download new track {title}: {dl_err}"
                                        )
                                        self._notify(
                                            f"Failed: {title} ({dl_err})"
                                        )
                except Exception as e:
                    logger.error(f"Error syncing playlist {url}: {e}")
                    self._notify(f"Error syncing playlist: {e}")

            self._stop_event.wait(self.interval_seconds)

    def stop(self):
        self._stop_event.set()
        self._notify("Playlist Watchdog stopped.")