import json
import logging
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ARCHIVE_FILE = Path("downloaded_archive.json")


def load_archive() -> dict[str, Any]:
    if ARCHIVE_FILE.exists():
        try:
            with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
            logger.warning(f"Could not load archive file: {e}")
            return {}
    return {}


def save_archive(archive: dict[str, Any]) -> None:
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8', dir=ARCHIVE_FILE.parent)
    try:
        json.dump(archive, temp_file, indent=4, ensure_ascii=False)
        temp_file.close()
        shutil.move(temp_file.name, ARCHIVE_FILE)
    except (OSError, IOError) as e:
        logger.error(f"Failed to save archive: {e}")
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        raise


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
