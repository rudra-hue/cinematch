"""Download movie posters from poster_url and save them as local files.

This script reads movie_data.csv and writes poster images into assets/images
using the movie_id as the filename. The app then loads posters locally, so it
never depends on remote image hotlinks at runtime.
"""

from __future__ import annotations

import csv
from pathlib import Path

import requests

CSV_FILE = Path(__file__).with_name("movie_data.csv")
IMAGE_DIR = Path(__file__).with_name("assets") / "images"
TIMEOUT_SECONDS = 30


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    with CSV_FILE.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        print("No movies found in movie_data.csv")
        return

    downloaded = 0
    skipped = 0
    failed = 0

    for row in rows:
        movie_id = str(row.get("movie_id", "")).strip()
        poster_url = str(row.get("poster_url", "")).strip()
        if not movie_id or not poster_url.startswith("http"):
            skipped += 1
            continue

        poster_path = IMAGE_DIR / f"{movie_id}.jpg"
        if poster_path.exists() and poster_path.stat().st_size > 0:
            skipped += 1
            continue

        try:
            response = requests.get(poster_url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            poster_path.write_bytes(response.content)
            downloaded += 1
            print(f"Downloaded {movie_id}: {row.get('title', '')}")
        except Exception as exc:
            failed += 1
            print(f"Failed {movie_id}: {row.get('title', '')} -> {exc}")

    print(f"Done. Downloaded={downloaded}, skipped={skipped}, failed={failed}")


if __name__ == "__main__":
    main()
