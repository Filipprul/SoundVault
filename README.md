# SoundVault

SoundVault is a CLI audio downloader built with Python, yt-dlp, and FFmpeg. It supports downloading audio streams, converting them to MP3, FLAC, or WAV, embedding ID3 metadata, and extracting cover art. It also includes an event callback system for future GUI implementations.

## Features

- Download and convert audio to MP3, FLAC, or WAV using FFmpeg.
- Embed ID3 metadata and cover art automatically.
- Network connectivity checks and error handling.
- Configurable via config.json.
- Event callbacks (progress_callback, status_callback) for GUI integration.
- PEP8 linting via Ruff and automated tests via GitHub Actions.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Filipprul/SoundVault.git
   cd SoundVault
   
## Disclaimer

SoundVault is intended solely for personal use and for downloading 
or backing up user-owned or royalty-free audio content. 
Please respect the copyright of content creators and comply 
with the terms of service of the respective platforms. 
The developer assumes no liability for any unauthorized 
or illegal use of this software.