import requests
from mutagen.id3 import APIC, ID3, TALB, TDRC, TIT2, TPE1, error
from mutagen.mp3 import MP3


def fetch_metadata_from_musicbrainz(clean_title: str):
    url = "https://musicbrainz.org/ws/2/recording/"
    headers = {"User-Agent": "SoundVault/1.0 (contact@soundvault.local)"}

    if " - " in clean_title:
        parts = clean_title.split(" - ", 1)
        artist_query = parts[0].strip()
        track_query = parts[1].strip()
        query_str = f'recording:"{track_query}" AND artist:"{artist_query}"'
    else:
        query_str = clean_title

    params = {"query": query_str, "fmt": "json", "limit": 1}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            recordings = data.get("recordings", [])

            if not recordings and " - " in clean_title:
                params["query"] = clean_title
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    recordings = data.get("recordings", [])

            if recordings:
                rec = recordings[0]
                title = rec.get("title")
                artist = rec["artist-credit"][0]["name"] if "artist-credit" in rec else "Unknown Artist"

                releases = rec.get("releases", [])
                release = releases[0] if releases else {}
                album = release.get("title", "Unknown Album")
                date = release.get("date", "")[:4]
                release_id = release.get("id")

                cover_url = get_cover_art_url(release_id)
                return {
                    "title": title,
                    "artist": artist,
                    "album": album,
                    "year": date,
                    "cover_url": cover_url
                }
    except Exception as e:
        print(f"Fehler bei MusicBrainz API: {e}")
    return None


def get_cover_art_url(release_id: str):
    if not release_id:
        return None
    url = f"https://coverartarchive.org/release/{release_id}/front"
    try:
        res = requests.head(url, allow_redirects=True)
        if res.status_code == 200:
            return res.url
    except Exception: # noqa: S110
        pass
    return None


def apply_id3_tags(file_path: str, metadata: dict):
    try:
        audio = MP3(file_path, ID3=ID3)
        try:
            audio.add_tags()
        except error:
            pass

        if metadata.get("title"):
            audio.tags.add(TIT2(encoding=3, text=metadata["title"]))
        if metadata.get("artist"):
            audio.tags.add(TPE1(encoding=3, text=metadata["artist"]))
        if metadata.get("album"):
            audio.tags.add(TALB(encoding=3, text=metadata["album"]))
        if metadata.get("year"):
            audio.tags.add(TDRC(encoding=3, text=metadata["year"]))

        cover_url = metadata.get("cover_url")
        if cover_url:
            img_data = requests.get(cover_url).content
            audio.tags.add(
                APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc='Cover',
                    data=img_data
                )
            )

        audio.save()
        print("ID3 Tags & Cover erfolgreich geschrieben!")
    except Exception as e:
        print(f"Fehler beim Schreiben der ID3-Tags: {e}")