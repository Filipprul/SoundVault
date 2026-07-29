import os
import yt_dlp

# Target YouTube playlist URL to download audio track from
PLAYLIST_URL = "";

# Set up absolute paths relative to the current script directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIRECTORY = os.path.join(BASE_DIR, "")

# yt-dlp Configuration Dictionary
ydl_opts = {
    # Extract the highest quality available audio stream
    'format': 'bestaudio/best',

    # Define file output path and naming template (e.g., downloads/SongTitle.ext)
    'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, '%(title)s.%(ext)s'),

    # Skip videos that throw errors (e.g., private or region-locked tracks) instead of stopping execution
    'ignoreerrors': True,

    # Keep track of unique YouTube video IDs to skip previously downloaded tracks instantly
    'download_archive': os.path.join(BASE_DIR, 'archive.txt'),

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

print("Starting playlist download...")

# Initialize YoutubeDL client with specified options and execute batch download
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([PLAYLIST_URL])

print("\nProcess finished successfully!")