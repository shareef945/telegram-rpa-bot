import os
import re


def sanitize_name(name):
    name = re.sub(r"\.", " ", name)
    return re.sub(r"[^\w\s-]", "", name).strip()


def get_dynamic_path(file_name):
    name, extension = os.path.splitext(file_name)

    # Check if it's a TV show
    tv_match = re.search(r"(.*?)S(\d+)E(\d+)", name, re.IGNORECASE)
    if tv_match:
        show_name = sanitize_name(tv_match.group(1).strip())
        season = int(tv_match.group(2))
        episode = int(tv_match.group(3))
        plex_file_name = f"{show_name} - s{season:02d}e{episode:02d}{extension.lower()}"
        return os.path.join(
            "tv-shows", show_name, f"Season {season:02d}", plex_file_name
        )
    else:
        # If not a TV show, assume it's a movie
        movie_match = re.search(r"(.*?)(\d{4})", name)
        if movie_match:
            movie_name = sanitize_name(movie_match.group(1).strip())
            year = movie_match.group(2)
            plex_file_name = f"{movie_name} ({year}){extension.lower()}"
        else:
            movie_name = sanitize_name(name)
            plex_file_name = f"{movie_name}{extension.lower()}"
        return os.path.join("movies", plex_file_name)
