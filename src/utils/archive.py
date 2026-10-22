import json
from datetime import datetime
from pathlib import Path

ARCHIVE_FILE = Path("downloaded_archive.json")


def load_archive() -> dict:
    if ARCHIVE_FILE.exists():
        try:
            with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_archive(archive: dict) -> None:
    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive, f, indent=4, ensure_ascii=False)


def is_downloaded(video_id: str) -> bool:
    archive = load_archive()
    return video_id in archive


def mark_as_downloaded(video_id: str, title: str = "") -> None:
    archive = load_archive()
    archive[video_id] = {
        "title": title,
        "downloaded_at": datetime.now().isoformat(),
    }
    save_archive(archive)
