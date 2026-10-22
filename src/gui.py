import json
import threading
from pathlib import Path

import customtkinter as ctk

from src.downloader import SoundVaultDownloader
from src.watchdog import PlaylistWatchdog

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


def load_config() -> dict:
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


class SoundVaultApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("SoundVault - Audio Downloader")
        self.geometry("600x420")
        self.resizable(False, False)

        # Watchdog beim GUI-Start initialisieren
        config = load_config()
        playlists = config.get("monitored_playlists", [])
        interval = config.get("watchdog_interval_seconds", 1800)

        self.watchdog = PlaylistWatchdog(
            playlist_urls=playlists,
            interval_seconds=interval,
            status_callback=lambda msg: self.after(0, lambda: self.status_label.configure(text=msg)),
        )
        self.watchdog.start()

        self._create_widgets()

    def destroy(self):
        # Watchdog beim Schließen der App sauber beenden
        if hasattr(self, "watchdog"):
            self.watchdog.stop()
        super().destroy()

    def _create_widgets(self):
        self.title_label = ctk.CTkLabel(
            self, text="SoundVault", font=ctk.CTkFont(size=26, weight="bold")
        )
        self.title_label.pack(padx=20, pady=(20, 5))

        self.subtitle_label = ctk.CTkLabel(
            self,
            text="Cross-Platform Audio Extraction Engine",
            font=ctk.CTkFont(size=12),
        )
        self.subtitle_label.pack(padx=20, pady=(0, 20))

        self.url_entry = ctk.CTkEntry(
            self, placeholder_text="Paste URL here...", width=500, height=40
        )
        self.url_entry.pack(padx=20, pady=10)

        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(padx=20, pady=10, fill="x")

        self.format_label = ctk.CTkLabel(self.options_frame, text="Format:")
        self.format_label.grid(row=0, column=0, padx=10, pady=10)

        self.format_option = ctk.CTkOptionMenu(
            self.options_frame, values=["mp3", "m4a", "flac", "wav", "opus"]
        )
        self.format_option.grid(row=0, column=1, padx=10, pady=10)
        self.format_option.set("mp3")

        self.quality_label = ctk.CTkLabel(self.options_frame, text="Quality:")
        self.quality_label.grid(row=0, column=2, padx=10, pady=10)

        self.quality_option = ctk.CTkOptionMenu(
            self.options_frame, values=["320", "256", "192", "128"]
        )
        self.quality_option.grid(row=0, column=3, padx=10, pady=10)
        self.quality_option.set("320")

        self.download_btn = ctk.CTkButton(
            self,
            text="Start Download",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.start_download_thread,
        )
        self.download_btn.pack(padx=20, pady=15)

        self.progress_bar = ctk.CTkProgressBar(self, width=500)
        self.progress_bar.pack(padx=20, pady=(10, 5))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            self, text="Ready", font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(padx=20, pady=5)

    def start_download_thread(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status_label.configure(
                text="Please enter a valid URL!", text_color="red"
            )
            return

        self.download_btn.configure(state="disabled")
        self.status_label.configure(
            text="Starting download...", text_color="white"
        )
        self.progress_bar.set(0.0)

        thread = threading.Thread(
            target=self.run_download, args=(url,), daemon=True
        )
        thread.start()

    def update_progress(self, d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)

            if total and total > 0:
                percent = downloaded / total
                percent_display = f"{percent * 100:.1f}%"
            else:
                percent_str = d.get("_percent_str", "0%")
                clean_str = "".join(
                    c for c in percent_str if c.isdigit() or c == "."
                )
                try:
                    percent = float(clean_str) / 100
                    percent_display = f"{percent * 100:.1f}%"
                except ValueError:
                    percent = 0.0
                    percent_display = "0%"

            speed = d.get("_speed_str", "N/A").strip()

            self.after(0, lambda: self.progress_bar.set(percent))
            self.after(
                0,
                lambda: self.status_label.configure(
                    text=f"Downloading... {percent_display} ({speed})"
                ),
            )

    def run_download(self, url):
        try:
            audio_format = self.format_option.get()
            quality = self.quality_option.get()

            downloader = SoundVaultDownloader(
                progress_callback=self.update_progress,
                status_callback=lambda msg: self.after(
                    0, lambda: self.status_label.configure(text=msg)
                ),
            )

            downloader.config["audio_format"] = audio_format
            downloader.config["audio_quality"] = quality
            downloader.download(url)

            self.after(
                0,
                lambda: self.status_label.configure(
                    text="Download completed successfully!", text_color="green"
                ),
            )
            self.after(0, lambda: self.progress_bar.set(1.0))
        except Exception as e:
            err_msg = str(e)
            self.after(
                0,
                lambda: self.status_label.configure(
                    text=f"Error: {err_msg}", text_color="red"
                ),
            )
        finally:
            self.after(0, lambda: self.download_btn.configure(state="normal"))


if __name__ == "__main__":
    app = SoundVaultApp()
    app.mainloop()