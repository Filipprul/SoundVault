from src.utils.title_cleaner import clean_title
from src.utils.metadata_handler import fetch_metadata_from_musicbrainz, apply_id3_tags

raw_title = "Linkin Park - Numb [Official Music Video] (HD)"
cleaned = clean_title(raw_title)
print(f"Original: {raw_title}")
print(f"Bereinigt: {cleaned}")
print("-" * 40)

metadata = fetch_metadata_from_musicbrainz(cleaned)
print("Abgeholte Metadaten:", metadata)
print("-" * 40)
