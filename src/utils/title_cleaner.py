import re


def clean_title(title: str) -> str:
    patterns = [
        r'\s*[\(\[].*?(official|music|video|audio|lyrics|lyric|hd|4k|remix|live|visualizer|explicit).*?[\)\]]',
        r'\s*-\s*(official video|official music video|lyrics|audio)',
        r'\s*\|.*$'
    ]

    cleaned = title
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    return cleaned.strip()