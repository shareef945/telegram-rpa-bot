import os
import re


def sanitize_name(name):
    return re.sub(r"[^\w\-]", "", name.replace(" ", "-")).lower()


def get_dynamic_path(file_name):
    name, extension = os.path.splitext(file_name)

    tv_match = re.search(r"(.*?)S(\d+)E(\d+)", name, re.IGNORECASE)
    if tv_match:
        show_name = sanitize_name(tv_match.group(1).strip())
        season = int(tv_match.group(2))
        episode = int(tv_match.group(3))
        return os.path.join(
            "tv-shows",
            show_name,
            f"s{season:02d}",
            f"e{episode:02d}{extension.lower()}",
        )
    else:
        year_match = re.search(r"\.(\d{4})\.", name)
        year = year_match.group(1) if year_match else "unknown-year"
        movie_name = sanitize_name(name)
        return os.path.join("movies", year, f"{movie_name}{extension.lower()}")
