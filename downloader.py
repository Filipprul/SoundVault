import os
import yt_dlp

class SoundVaultDownloader:
    def __init__(self, download_dir = "downloads"):
        # "C:\Filipps Fotos-Videos"
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.download_directory = os.path.join(self.base_dir, download_dir)
        self.archive_file = os.path.join(self.base_dir, 'archive.txt')

    def download(self, playlist_url):
        ydl_opts = {
            # Extract the highest quality available audio stream
            'format': 'bestaudio/best',

            # Define file output path and naming template (e.g., downloads/SongTitle.ext)
            'outtmpl': os.path.join(self.download_directory, '%(title)s.%(ext)s'),

            # Skip videos that throw errors (e.g., private or region-locked tracks) instead of stopping execution
            'ignoreerrors': True,

            # Keep track of unique YouTube video IDs to skip previously downloaded tracks instantly
            'download_archive': self.archive_file,

            # Post-processing chain applied sequentially after raw audio download completes
            'postprocessors': [
                # Step 1: Extract audio and convert it to high-quality 320 kbps MP3 format via FFmpeg
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                },
                # Step 2: Write standard ID3 metadata tags (Title, Artist, Album) to the MP3 file
                {'key': 'FFmpegMetadata'},

                # Step 3: Embed the downloaded video thumbnail directly into the MP3 ID3 cover art tag
                {'key': 'EmbedThumbnail'},
            ],

            # Enable temporary thumbnail downloading required by the EmbedThumbnail postprocessor
            'writethumbnail': True,
        }

        # Initialize YoutubeDL client with specified options and execute batch download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([playlist_url])