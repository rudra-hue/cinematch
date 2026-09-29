"""
recommender.py  -  the "brain" of CineMatch
=============================================
This file contains ONLY the recommendation logic (no Streamlit code).

Type of recommender : Content-Based Filtering
Machine-learning    : TF-IDF Vectorizer + Cosine Similarity  (scikit-learn)

IDEA IN ONE SENTENCE
    If two movies use similar words (genres, story words, director, actors),
    they are probably similar movies.

STEPS
    1. Load the movies from movie_data.csv
    2. Combine genres + overview + director + cast into ONE text per movie
    3. Clean that text
    4. TF-IDF   : turn each text into a list of numbers (a vector)
    5. Cosine similarity : compare every movie with every other movie
    6. For the chosen movie, return the movies with the highest similarity
"""

import re
from functools import lru_cache
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# The CSV file lives in the same folder as this file.
DATA_FILE = Path(__file__).parent / "movie_data.csv"

# Columns we expect in the CSV file.
COLUMNS = ["movie_id", "title", "overview", "genres", "rating", "release_year",
           "language", "director", "cast", "poster_url", "streaming_platform"]


def _has_local_poster(movie_id):
    """Return True when a local poster image exists for this movie."""
    movie_id = str(movie_id).strip()
    if not movie_id:
        return False
    poster_folder = Path(__file__).parent / "assets" / "images"
    for extension in (".jpg", ".jpeg", ".png", ".webp"):
        if (poster_folder / f"{movie_id}{extension}").exists():
            return True
    return False


# ---------------------------------------------------------------------------
# STEP 1 - Load the data
# ---------------------------------------------------------------------------
def load_movies():
    """Read movie_data.csv into a pandas DataFrame.

    If the file is missing or empty we return an EMPTY table instead of
    crashing, so the app can show a friendly message.
    """
    try:
        movies = pd.read_csv(DATA_FILE)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=COLUMNS)

    # Text columns: replace missing values (NaN) with an empty string.
    text_columns = ["title", "overview", "genres", "language", "director",
                    "cast", "poster_url", "streaming_platform"]
    for col in text_columns:
        if col not in movies.columns:
            movies[col] = ""
        movies[col] = movies[col].fillna("").astype(str)

    # Number columns: make sure they really are numbers.
    movies["rating"] = pd.to_numeric(movies.get("rating"), errors="coerce").fillna(0.0)
    movies["release_year"] = pd.to_numeric(movies.get("release_year"), errors="coerce").fillna(0).astype(int)
    if "movie_id" not in movies.columns:
        movies["movie_id"] = range(1, len(movies) + 1)

    # A movie without a title is useless, so drop it.
    movies = movies[movies["title"].str.strip() != ""]

    # Only keep movies that have a local poster image. This avoids broken or
    # placeholder-only entries in the UI.
    movies = movies[movies["movie_id"].apply(_has_local_poster)]
    return movies.reset_index(drop=True)


# ---------------------------------------------------------------------------
# STEP 2 + 3 - Combine and clean the text
# ---------------------------------------------------------------------------
def clean_text(text):
    """Make free text (like the overview) simple: lowercase, no punctuation.

    "A Thief, who steals..."  ->  "a thief who steals"
    """
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)   # remove punctuation
    return re.sub(r"\s+", " ", text).strip()   # remove extra spaces


def clean_names(names):
    """Clean a '|' separated list of names or genres.

    We remove the spaces INSIDE each name so that a name stays ONE word:
        "Christopher Nolan|Michael Caine"  ->  "christophernolan michaelcaine"
        "Sci-Fi|Drama"                     ->  "scifi drama"
    Why? Otherwise "Christopher" would match every movie with any Christopher.
    """
    parts = [re.sub(r"[^a-z0-9]", "", name.lower()) for name in str(names).split("|")]
    return " ".join(p for p in parts if p)


def combine_features(movies):
    """Build one text string ("soup") per movie from genres + overview + director + cast."""
    genres = movies["genres"].apply(clean_names)
    overview = movies["overview"].apply(clean_text)
    director = movies["director"].apply(clean_names)
    cast = movies["cast"].apply(clean_names)

    # Genres are written twice so that they count a little more than
    # a single random word from the overview.
    return genres + " " + genres + " " + overview + " " + director + " " + cast


# ---------------------------------------------------------------------------
# STEP 4 + 5 - TF-IDF and cosine similarity
# ---------------------------------------------------------------------------
def build_similarity_matrix(soup):
    """Turn the text into numbers (TF-IDF) and compare all movies (cosine similarity).

    TF-IDF  (Term Frequency - Inverse Document Frequency)
        Gives every word a score for every movie.
        * TF  : a word used often in this movie's text gets a higher score.
        * IDF : a word that is RARE across all movies gets a higher score,
                a very common word (like "drama") gets a lower score.
        So special words ("wormhole", "astronaut") matter more than common ones.
        Result: each movie becomes a vector (a row of numbers).

    Cosine similarity
        Measures the angle between two vectors.
            1.0 -> exactly the same direction  (very similar movies)
            0.0 -> nothing in common
        We do it for every pair, giving a table (matrix) of size
        (number of movies) x (number of movies).
    """
    vectorizer = TfidfVectorizer(stop_words="english")  # ignore words like "the", "and", "of"
    tfidf_matrix = vectorizer.fit_transform(soup)
    return cosine_similarity(tfidf_matrix)


@lru_cache(maxsize=1)
def _build_model():
    """Load data and build the similarity table ONCE, then remember the result.

    (@lru_cache means: "run this function the first time, then reuse the answer",
    so the app stays fast when the user clicks around.)
    """
    movies = load_movies()
    if movies.empty:
        return movies, None
    soup = combine_features(movies)
    similarity = build_similarity_matrix(soup)
    return movies, similarity


def get_movies():
    """Return the full movie table (a copy, so nobody changes the original)."""
    movies, _ = _build_model()
    return movies.copy()


# ---------------------------------------------------------------------------
# STEP 6 - Get the recommendations
# ---------------------------------------------------------------------------
def get_recommendations(movie_title, n=6):
    """Return the n movies most similar to `movie_title` (best match first).

    This is the simple ML recommendation step: we turn movie text into TF-IDF
    vectors and then use cosine similarity to measure how close two movie
    descriptions are. The result is easy to explain to a manager or professor.
    """
    movies, similarity = _build_model()
    empty = pd.DataFrame(columns=COLUMNS + ["similarity"])

    if movies.empty or similarity is None:
        return empty

    # Find the row number of the chosen movie (ignore upper/lower case).
    matches = movies.index[movies["title"].str.lower() == str(movie_title).strip().lower()]
    if len(matches) == 0:
        return empty
    movie_index = matches[0]

    # (row number, similarity score) for every movie, best score first.
    scores = list(enumerate(similarity[movie_index]))
    scores.sort(key=lambda pair: pair[1], reverse=True)

    # Remove the movie itself and movies with score 0, then keep the top n.
    top = [(i, s) for i, s in scores if i != movie_index and s > 0][:n]
    if not top:
        return empty

    result = movies.iloc[[i for i, _ in top]].copy()
    result["similarity"] = [round(float(s), 3) for _, s in top]
    return result.reset_index(drop=True)


def predict(movie_title, n=8):
    """Simple ML prediction for similar movies.

    This is the function used by the UI for the 'More like this' button.
    It explains clearly: text -> TF-IDF vectors -> cosine similarity -> top matches.
    """
    return get_recommendations(movie_title, n=n)


# Quick test:  python recommender.py
if __name__ == "__main__":
    for title in ["Interstellar", "The Godfather", "3 Idiots"]:
        print(f"\nBecause you liked {title}:")
        print(get_recommendations(title, n=6)[["title", "release_year", "similarity"]].to_string(index=False))
