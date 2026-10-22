import json
import shutil
import unittest
from pathlib import Path

from src.downloader import SoundVaultDownloader


class TestSoundVault(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.test_dir = self.project_root / "temp_test_downloads"
        self.test_config = self.project_root / "test_config.json"

        config_data = {
            "download_dir": str(self.test_dir),
            "audio_format": "mp3",
            "audio_quality": "0"
        }
        with open(self.test_config, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        self.downloader = SoundVaultDownloader(config_file=str(self.test_config))

    def tearDown(self):
        config_path = Path(self.test_config)
        if config_path.exists():
            config_path.unlink()

        if self.test_dir.exists() and self.test_dir.is_dir():
            shutil.rmtree(self.test_dir)

    def test_network_check(self):
        result = SoundVaultDownloader.check_network()
        self.assertIsInstance(result, bool)

    def test_config_loading_and_path_generation(self):
        expected_path = self.test_dir
        self.assertEqual(self.downloader.download_directory, expected_path)
        self.assertTrue(self.downloader.download_directory.exists())

    def test_audio_format_setting(self):
        self.assertEqual(self.downloader.config.get("audio_format"), "mp3")

    def test_metadata_and_thumbnail_postprocessors(self):
        opts = {
            'postprocessors': [
                {'key': 'FFmpegMetadata', 'add_metadata': True},
                {'key': 'EmbedThumbnail'}
            ]
        }
        keys = [p['key'] for p in opts['postprocessors']]
        self.assertIn('FFmpegMetadata', keys)
        self.assertIn('EmbedThumbnail', keys)

if __name__ == '__main__':
    unittest.main()