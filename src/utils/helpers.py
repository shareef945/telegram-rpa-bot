import os
import re


def sanitize_name(name):
    name = re.sub(r"\.", " ", name)
    return re.sub(r"[^\w\s-]", "", name).strip()


def format_size(size_bytes):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0


def get_dynamic_path(file_name):
    name, extension = os.path.splitext(file_name)

    # Check if it's a TV show
    tv_match = re.search(r"(.*?)S(\d+)E(\d+)", name, re.IGNORECASE)
    if tv_match:
        show_name = sanitize_name(tv_match.group(1).strip())
        season = int(tv_match.group(2))
        episode = int(tv_match.group(3))

        # Extract quality if present in square brackets
        quality_match = re.search(r"\[(.*?)\]", name)
        quality_suffix = f" [{quality_match.group(1)}]" if quality_match else ""

        plex_file_name = f"{show_name} - s{season:02d}e{episode:02d}{quality_suffix}{extension.lower()}"

        # Check if year is present in show name
        year_match = re.search(r"(.*?)\((\d{4})\)", show_name)
        if year_match:
            show_folder = f"{year_match.group(1).strip()} ({year_match.group(2)})"
        else:
            show_folder = show_name

        return os.path.join(
            "tv-shows", show_folder, f"Season {season:02d}", plex_file_name
        )
    else:
        # Updated movie handling to match Radarr format
        movie_match = re.search(r"(.*?)(\d{4})", name)
        if movie_match:
            movie_name = sanitize_name(movie_match.group(1).strip())
            year = movie_match.group(2)

            # Extract quality if present in square brackets
            quality_match = re.search(r"\[(.*?)\]", name)
            quality_suffix = f" {quality_match.group(1)}" if quality_match else ""

            plex_file_name = f"{movie_name} ({year}){quality_suffix}{extension.lower()}"
        else:
            movie_name = sanitize_name(name)
            # Extract quality if present in square brackets
            quality_match = re.search(r"\[(.*?)\]", name)
            quality_suffix = f" {quality_match.group(1)}" if quality_match else ""
            plex_file_name = f"{movie_name}{quality_suffix}{extension.lower()}"

        return os.path.join("movies", plex_file_name)
