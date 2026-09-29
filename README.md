# 🎬 CineMatch — Movie Recommendation & Streaming Finder

A college project built with **Python, Streamlit, Pandas and Scikit-learn**.
Pick a movie → CineMatch recommends similar movies and shows where to watch them.

---

## How to run

```bash
# 1. (optional) create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac / Linux

# 2. install the packages
pip install -r requirements.txt

# 3. start the app (run this inside the CineMatch folder)
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.
To test only the recommender (no web page): `python recommender.py`

---

## Project structure

```text
CineMatch/
│
├── app.py                  ← The web page (Streamlit user interface)
├── recommender.py          ← The machine-learning part (TF-IDF + cosine similarity)
├── movie_data.csv          ← The movie dataset (252 movies)
├── requirements.txt        ← List of packages to install
├── README.md               ← This file
├── .streamlit/
│   └── config.toml         ← Dark + gold colour theme for Streamlit
└── assets/
    └── images/             ← (optional) put real poster images here
```

| File | What it does |
|---|---|
| `app.py` | Shows everything on screen: search box, movie details, recommendation cards, genre buttons, streaming finder, filters, watchlist. It calls `recommender.py` to get the recommendations. |
| `recommender.py` | Loads the CSV, cleans the text, runs TF-IDF, calculates cosine similarity and returns the most similar movies. It has **no** Streamlit code, so it is easy to test alone. |
| `movie_data.csv` | The dataset. One row = one movie. |
| `requirements.txt` | `streamlit`, `pandas`, `scikit-learn`. |
| `.streamlit/config.toml` | Only sets the theme colours (dark background, gold buttons/sliders). |
| `assets/images/` | If you add poster pictures named `1.jpg`, `2.jpg`… (the `movie_id`), they are shown automatically. |

---

## Dataset format (`movie_data.csv`)

| Column | Example | Notes |
|---|---|---|
| `movie_id` | `1` | Unique number |
| `title` | `Interstellar` | |
| `overview` | `A former pilot joins astronauts…` | Short story summary (written in our own words) |
| `genres` | `Sci-Fi\|Drama\|Adventure` | Separated by `\|` |
| `rating` | `8.7` | Approximate IMDb-style rating |
| `release_year` | `2014` | |
| `language` | `English` | |
| `director` | `Christopher Nolan` | |
| `cast` | `Matthew McConaughey\|Anne Hathaway\|…` | Separated by `\|` |
| `poster_url` | *(empty)* | Optional web link to a poster. If empty, CineMatch looks in `assets/images/`, and if there is no image it draws a vintage title poster. |
| `streaming_platform` | `Netflix\|Prime Video` | **Demo / sample data** – see the warning below |

> ⚠️ **About the streaming data:** the `streaming_platform` column is **sample data made up for the demonstration**. It is *not* live and *not* verified. Real availability changes by country and over time. The app labels it as demo data everywhere it is shown.
> Ratings are approximate; please double-check any figure you quote in your report.

---

## 1. Introduction

CineMatch is a small web application that helps people choose a movie. The user selects a movie they like, and CineMatch suggests similar movies and shows on which streaming platforms they can be watched.

## 2. Problem Statement

People spend a lot of time deciding what movie to watch, and they often do not know where a movie is available to stream.

## 3. Objective

To recommend movies similar to the one the user selects, and to show the available streaming platforms for each movie.

## 4. Technology Used

| Technology | Why we use it |
|---|---|
| **Python** | Main programming language |
| **Streamlit** | Builds the web page using only Python |
| **Pandas** | Reads the CSV file and filters/sorts movie tables |
| **Scikit-learn** | Provides `TfidfVectorizer` and `cosine_similarity` |

## 5. Algorithm — Content-Based Filtering

Content-based filtering recommends items by comparing their **content**. Here the content of a movie is its genres, story (overview), director and cast. If two movies have similar content, they are recommended together.
(It does not need any user data, so there are no accounts or ratings from users.)

## 6. Machine Learning — TF-IDF + Cosine Similarity

**Step A – Make one text per movie.** We join `genres + overview + director + cast`, then clean it (lowercase, remove punctuation). Names are joined into single words (`christophernolan`) so "Christopher" alone does not match every Christopher.

**Step B – TF-IDF (Term Frequency – Inverse Document Frequency).** Computers cannot compare sentences, so we convert each text into numbers.
- **TF**: how often a word appears in this movie's text.
- **IDF**: how *rare* the word is across all movies. Rare words (like `wormhole`) get a high score; very common words (like `drama`) get a lower score.

Each movie becomes a **vector** (a list of numbers).

**Step C – Cosine similarity.** It measures the angle between two vectors.
`1.0` = very similar, `0.0` = nothing in common.
We calculate it for every pair of movies (a 252 × 252 table) and, for the selected movie, pick the highest scores.

**Tiny example**

| Movie | Text (simplified) |
|---|---|
| A | `space astronaut planet` |
| B | `space astronaut mars` |
| C | `love wedding paris` |

A and B share the words *space* and *astronaut* → high similarity. A and C share nothing → similarity 0. So B is recommended for A.

## 7. System Workflow

```text
User selects movie
       ↓
Movie information
       ↓
TF-IDF conversion
       ↓
Cosine similarity
       ↓
Similar movies
       ↓
Recommendations
       ↓
Streaming platform
```

In code: `app.py` calls `get_recommendations(title)` in `recommender.py`, which returns a table sorted by similarity. `app.py` then draws the top 6 as movie cards.

## 8. Future Scope

- Live streaming availability (for example from a streaming-availability API)
- User accounts
- Personalized recommendations (using each user's ratings/history)
- AI chatbot ("suggest a sad movie for a rainy day")
- Mobile application
- More advanced recommendation algorithms (collaborative filtering, embeddings)

---

## Features checklist

- ✅ Movie search/select box, with a detailed "ticket-style" information section
- ✅ "You may also like": top 6 similar movies (real TF-IDF + cosine similarity, not hard-coded)
- ✅ "How were these picked?" panel that shows the similarity scores (great for your demo)
- ✅ Explore by genre (8 genre buttons)
- ✅ Where can I watch? (streaming finder, demo data clearly labelled)
- ✅ Sidebar filters: genre, language, minimum rating, release year, streaming platform
- ✅ The Classics and Popular Picks sections
- ✅ Watchlist stored in `st.session_state` (no database, no login; it resets when the page is refreshed)
- ✅ Friendly messages for: movie not found, missing poster, no recommendations, missing streaming info, empty dataset

## Adding real posters (optional)

Two easy ways:
1. Paste an image link in the `poster_url` column of `movie_data.csv`, **or**
2. Save the image as `assets/images/<movie_id>.jpg` (for example `1.jpg` for Interstellar).

If you edit the CSV, stop the app (Ctrl+C) and run it again.

## Adding more movies

Add new rows to `movie_data.csv` with the same columns (use `|` between genres and between cast members, and give a new unique `movie_id`). The recommender rebuilds itself automatically when the app restarts.

---

## Questions your teacher may ask

**Why content-based and not collaborative filtering?**
Collaborative filtering needs data about many users. We have no users, so we compare the movies themselves.

**What is TF-IDF in one line?**
It gives higher scores to words that are important for a movie and rare in other movies.

**Why cosine similarity and not distance?**
It compares the *direction* of vectors, so a long overview and a short overview can still be compared fairly.

**Is the recommendation hard-coded?**
No. The similarity is calculated by the algorithm every time from the CSV data. Change the data and the recommendations change.

**Is the streaming information real?**
No. It is demo/sample data in the CSV, and the app says so. Live data would need an external API (future scope).

**Why are genres written twice in the text?**
So genres count a little more than a single random word in the overview (see `combine_features` in `recommender.py`).

**What are the limitations?**
It only knows the words in the dataset, so it can miss a movie that is "similar" for reasons not written in the text (for example, a similar mood). The dataset is small (252 movies), and streaming data is sample data.
