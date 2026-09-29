"""
app.py  -  cinematch : Movie Recommendation & Streaming Finder
================================================================
This file is the USER INTERFACE (built with Streamlit).
The recommendation logic lives in recommender.py.

Run it with:   streamlit run app.py

Order of this file
    1. Settings and small constants
    2. Styling (CSS) - the "classic cinema" look
    3. Helper functions that build the HTML for posters and movie cards
    4. Watchlist helpers (Streamlit session state)
    5. The page itself, from top to bottom
"""

import base64
import html
import json
import random
import time
from urllib.parse import quote_plus
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from recommender import get_movies, predict

st.set_page_config(page_title="cinematch - Movie Recommendations", page_icon="🎞️", layout="wide")

# ---------------------------------------------------------------------------
# 1. SETTINGS AND CONSTANTS
# ---------------------------------------------------------------------------
IMAGE_FOLDER = Path(__file__).parent / "assets" / "images"

NOT_FOUND_MESSAGE = "This movie isn't in our vault yet."
DEMO_NOTE = ("Demo / sample availability data - not live. Streaming availability changes by "
             "country and over time, so always check the platform before you plan your evening.")

# (emoji, genre name as written in movie_data.csv)
GENRE_BUTTONS = [("🍿", "Action"), ("🚀", "Sci-Fi"), ("🎭", "Drama"), ("😂", "Comedy"),
                 ("⚡", "Thriller"), ("❤️", "Romance"), ("🕵️", "Crime"), ("🐉", "Fantasy"),
                 ("🧭", "Adventure"), ("👻", "Horror")]

CLASSIC_TITLES = ["The Godfather", "The Matrix", "Jurassic Park", "Inception", "The Dark Knight", "Goodfellas"]

# Platform bold colors for the new modern look
PLATFORM_COLORS = {"Netflix": "#E50914", "Prime Video": "#00A8E1", "JioHotstar": "#01147C",
                   "ZEE5": "#8A179E", "Sony LIV": "#FDA202", "Apple TV": "#E1E1E1"}

# Colour (hue) of the poster placeholder, chosen from the movie's first genre.
GENRE_ICON = {"Sci-Fi": "🚀", "Drama": "🎭", "Thriller": "🔪", "Comedy": "😂", "Romance": "❤️", "Horror": "👻",
              "Action": "💥", "Crime": "🕵️", "Adventure": "🧭", "Animation": "🎨", "Fantasy": "🐉",
              "Mystery": "🔎", "War": "🎖️", "Biography": "📜", "Music": "🎵", "Family": "🏠", "History": "🏛️"}

GENRE_HUE = {"Sci-Fi": 210, "Comedy": 42, "Thriller": 350, "Romance": 330, "Action": 18, "Drama": 280,
             "Crime": 250, "Adventure": 165, "Horror": 0, "Animation": 190, "Fantasy": 265,
             "Mystery": 240, "War": 95, "Biography": 38, "Music": 300, "Family": 50, "History": 34}

# ---------------------------------------------------------------------------
# 2. STYLING  (plain CSS injected into the page)
# ---------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;700;900&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --bg: #050816; 
    --panel: #0f172a; 
  --text: #f1f5f9; 
  --text-muted: #94a3b8;
    --accent: #22d3ee; 
    --accent-2: #6366f1;
    --accent-3: #14b8a6;
    --gradient: linear-gradient(135deg, var(--accent), var(--accent-3) 45%, var(--accent-2));
  --font-display: 'Outfit', system-ui, sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;
}

/* Base styles */
.stApp {
  background-color: var(--bg);
  background-image: radial-gradient(circle at 15% 10%, rgba(139, 92, 246, 0.15) 0%, transparent 40%),
                    radial-gradient(circle at 85% 60%, rgba(6, 182, 212, 0.15) 0%, transparent 40%);
  color: var(--text);
  font-family: var(--font-body);
}
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1400px; padding-top: 1rem; padding-bottom: 4rem; }
[data-testid="stSidebar"] { 
    background: rgba(17, 24, 39, 0.6); backdrop-filter: blur(20px); 
    border-right: 1px solid rgba(255,255,255,0.05); 
}

/* Hero Section */
.masthead {
  display: inline-block;
  font-family: var(--font-display); font-weight: 900; font-size: 1.5rem;
  letter-spacing: 0.25em; text-transform: uppercase;
  background: var(--gradient); -webkit-background-clip: text; color: transparent;
  padding: 0.5rem 1rem; border-radius: 99px; border: 1px solid rgba(255,255,255,0.1);
  background-color: rgba(255,255,255,0.02); margin: 0 auto 1.5rem;
}
.hero { text-align: center; padding: 2rem 0 1rem; display: flex; flex-direction: column; align-items: center; }
.hero h1 {
  font-family: var(--font-display)!important; font-weight: 900; color: #fff!important;
  font-size: clamp(2.5rem, 6vw, 4.5rem); line-height: 1.1; letter-spacing: -0.02em; margin: 0; padding: 0;
  text-wrap: balance; text-shadow: 0 4px 20px rgba(0,0,0,0.5);
}
.hero p {
  color: var(--text-muted); font-size: 1.25rem; max-width: 40rem; margin: 1.2rem auto 0;
  font-weight: 300; line-height: 1.6;
}
.tagline { display: none; }
.filmstrip { display: none; }
.prompt { text-align: center; font-family: var(--font-body); font-size: 1.25rem; margin: 3rem 0 0.5rem; color: #fff; font-weight: 500;}

/* Section Titles */
.section-title {
  margin: 3.5rem 0 0.5rem; font-family: var(--font-display); font-weight: 700; font-size: 2rem;
  color: #fff; display: block; width: 100%; border-bottom: 2px solid rgba(255,255,255,0.05);
  padding-bottom: 0.75rem;
}
.section-sub { color: var(--text-muted); font-size: 1.05rem; margin: 0 0 1.5rem; font-weight: 300; }

/* Posters & Cards (Glassmorphism) */
.movie-card {
  margin-bottom: 1.5rem;
  transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    transform-style: preserve-3d;
    perspective: 1200px;
}
.movie-card:hover { transform: translateY(-8px) rotateX(3deg); }

.poster-wrap {
  position: relative; aspect-ratio: 2/3; overflow: hidden; border-radius: 14px; background: #000;
  box-shadow: 0 10px 30px rgba(0,0,0,0.6), 0 14px 40px rgba(6,182,212,0.10);
  border: 1px solid rgba(255,255,255,0.12);
  transition: all 0.3s ease;
    transform-style: preserve-3d;
}
.movie-card:hover .poster-wrap {
  box-shadow: 0 20px 40px rgba(0,0,0,0.8), 0 0 0 2px rgba(6, 182, 212, 0.35);
  border-color: rgba(255,255,255,0.2);
    transform: translateZ(12px) scale(1.01);
}
.poster-img { width: 100%; height: 100%; object-fit: cover; display: block; }
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; box-shadow: inset 0 0 60px rgba(255,255,255, 0.1); }
  100% { background-position: 0% 50%; }
}

.poster-fallback {
    position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: space-between;
    align-items: center; text-align: center; padding: 12% 10% 10%;
  background: linear-gradient(-45deg, hsl(var(--h), 60%, 20%), hsl(calc(var(--h) + 40), 70%, 15%), hsl(calc(var(--h) - 40), 50%, 10%));
  background-size: 300% 300%;
  animation: gradientShift 5s ease infinite;
}
.pf-icon { font-size: clamp(3rem, 18cqw, 5rem); line-height: 1; opacity: 0.18; position: absolute; top:50%; transform:translateY(-50%); }
.pf-label {
    margin-top: 0.25rem;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.55);
}
.pf-title {
    font-family: var(--font-display); font-weight: 900; color: rgba(255,255,255,0.94);
    font-size: clamp(1rem, 4.2cqw, 1.85rem); line-height: 1.1; z-index: 2;
    text-shadow: 0 4px 12px rgba(0,0,0,0.8);
    display: -webkit-box;
    -webkit-line-clamp: 4;
    -webkit-box-orient: vertical;
    overflow: hidden;
    max-width: 92%;
}
.pf-bottom { font-family: var(--font-display); font-weight: 700; font-size: clamp(0.8rem, 3cqw, 1rem); color: rgba(255,255,255,0.55); z-index: 2;}

.overlay {
  position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: flex-end;
  padding: 1rem; opacity: 0;
  background: linear-gradient(0deg, rgba(8,12,23,0.95) 10%, rgba(8,12,23,0.7) 50%, transparent 100%);
  backdrop-filter: blur(2px);
  transition: opacity 0.3s ease; border-radius: 12px;
}
.movie-card:hover .overlay { opacity: 1; }
.overlay p { margin: 0; font-size: 0.85rem; line-height: 1.5; color: var(--text); font-weight:300; display: -webkit-box; -webkit-line-clamp: 6; -webkit-box-orient: vertical; overflow: hidden;}

/* Movie Card Info */
.card-title {
  font-family: var(--font-display); font-weight: 700; font-size: 1.15rem; line-height: 1.3;
  margin: 0.8rem 0 0.25rem; color: #fff;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.card-meta { display: flex; align-items: center; gap: 0.5rem; color: var(--text-muted); font-size: 0.85rem; margin-bottom:0.4rem; font-weight:500;}
.meta-rating { color: #f59e0b; display: flex; align-items: center; gap: 0.2rem;}
.card-genre { color: var(--accent); font-size: 0.8rem; font-weight: 500; margin-bottom: 0.5rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}

/* Platform Badges (Modern Pills) */
.badge {
  display: inline-flex; align-items: center; gap: 0.4rem; margin: 0 0.4rem 0.4rem 0; padding: 0.3rem 0.75rem;
  font-size: 0.75rem; font-weight: 600; color: #fff; 
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); 
  border-radius: 99px; backdrop-filter: blur(10px);
}
.badge .dot { width: 0.4rem; height: 0.4rem; border-radius: 50%; box-shadow: 0 0 8px currentColor;}
.badge.big { font-size: 0.95rem; padding: 0.4rem 1rem; }
.no-stream { color: var(--text-muted); font-size: 0.85rem; font-style: italic; background:rgba(255,255,255,0.03); padding:0.4rem 0.8rem; border-radius:8px;}

/* Detail Panel / Glass Ticket */
.ticket {
  display: flex; gap: 2.5rem; margin: 1.5rem 0 2rem; padding: 2rem;
  background: rgba(17, 24, 39, 0.4); backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.08); border-radius: 16px;
  box-shadow: 0 24px 60px rgba(0,0,0,0.4);
    transform: perspective(1200px) rotateX(1deg);
}
.ticket-poster { flex: 0 0 240px; }
.ticket-body { flex: 1; min-width: 0; display:flex; flex-direction:column;}
.admit { display: none; }
.ticket-title { font-family: var(--font-display); font-weight: 900; font-size: 3.2rem; line-height: 1.1; margin: 0 0 0.75rem; color: #fff; text-wrap:balance;}
.ticket-line { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem; color: var(--text-muted); font-size: 1.05rem; margin-bottom: 1.25rem; font-weight:500;}
.ticket-rating { background: rgba(245, 158, 11, 0.15); color: #f59e0b; padding: 0.3rem 0.75rem; border-radius: 8px; font-weight: 700; border: 1px solid rgba(245, 158, 11, 0.3);}
.ticket-tags { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; flex-wrap: wrap;}
.ticket-tag { background: rgba(6, 182, 212, 0.15); color: var(--accent); padding: 0.3rem 0.8rem; border-radius: 99px; font-size: 0.85rem; font-weight: 600; border: 1px solid rgba(6, 182, 212, 0.3); }
.ticket-overview { color: var(--text); line-height: 1.7; font-size:1.1rem; font-weight:300; max-width: 65ch; margin-bottom:2rem;}
.stub { display: flex; flex-wrap: wrap; gap: 2.5rem; padding-top: 1.5rem; border-top: 1px solid rgba(255,255,255,0.1); margin-top:auto;}
.stub small { display: block; color: var(--text-muted); font-size: 0.8rem; font-weight: 600; letter-spacing: 0.1em; text-transform:uppercase; margin-bottom: 0.4rem;}
.stub span { font-size: 1.05rem; font-weight: 500; color: #fff;}
@media (max-width: 800px) {
  .ticket { flex-direction: column; padding: 1.5rem; gap: 1.5rem;}
  .ticket-poster { flex-basis: auto; width: 220px; margin: 0 auto; }
  .ticket-title { font-size: 2.4rem; text-align:center;}
  .ticket-line, .ticket-tags { justify-content:center; }
  .ticket-overview { text-align:center; margin: 0 auto 1.5rem;}
  .stub { justify-content:center; text-align:center;}
}

/* UI Elements */
.demo-note {
  margin: 1rem 0; padding: 1rem 1.25rem; color: var(--text-muted); font-size: 0.9rem; border-radius: 12px;
  background: rgba(255,255,255,0.03); border-left: 4px solid var(--accent); line-height: 1.5;
}
.side-title { font-family: var(--font-display); font-weight: 700; font-size: 1.25rem; letter-spacing: 0.1em; color: #fff; margin-bottom: 1.5rem; text-transform:uppercase;}
.footer { text-align: center; color: var(--text-muted); font-size: 0.95rem; padding: 3rem 0; font-weight:300; border-top:1px solid rgba(255,255,255,0.05); margin-top:5rem;}

.movie-link {
    display: block;
    color: inherit;
    text-decoration: none;
}
.movie-link:hover .movie-card,
.movie-link:focus-visible .movie-card {
    transform: translateY(-10px) rotateX(4deg) rotateY(-1deg);
}
.movie-link:focus-visible {
    outline: none;
}

/* Enhance Streamlit Buttons & Inputs */
.stButton > button {
    width: 100%; min-height: 2.9rem; border-radius: 16px; font-family: var(--font-body); font-weight: 800; font-size: 0.98rem;
    transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease, background 0.22s ease; border: 1px solid rgba(255,255,255,0.12);
    background: linear-gradient(180deg, rgba(255,255,255,0.09), rgba(255,255,255,0.03));
    color: #e5eef8; box-shadow: 0 10px 22px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.14);
    transform: perspective(1000px) translateY(-1px) rotateX(6deg);
    position: relative;
    overflow: hidden;
}
.stButton > button:hover {
    border-color: rgba(255,255,255,0.4); background: rgba(255,255,255,0.1);
    transform: perspective(1000px) rotateX(0deg) translateY(-4px) scale(1.01);
    box-shadow: 0 16px 32px rgba(0,0,0,0.36), 0 0 20px rgba(34,211,238,0.14);
}
.stButton > button:active {
    transform: perspective(1000px) translateY(2px) scale(0.99);
    box-shadow: 0 8px 16px rgba(0,0,0,0.24), inset 0 1px 0 rgba(255,255,255,0.08);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, rgba(34,211,238,0.95), rgba(99,102,241,0.95));
    border: none; color: #fff; box-shadow: 0 14px 28px rgba(34,211,238,0.22), inset 0 1px 0 rgba(255,255,255,0.2);
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 18px 34px rgba(99, 102, 241, 0.34), 0 0 20px rgba(34,211,238,0.18);
  transform: perspective(1000px) rotateX(0deg) translateY(-5px) scale(1.02);
}
div[data-baseweb="select"] > div { border-color: rgba(255,255,255,0.1); border-radius: 12px; background: rgba(0,0,0,0.3) !important; transition: border-color 0.2s; }
div[data-baseweb="select"] > div:hover { border-color: var(--accent); }
[data-testid="stMain"] div[data-baseweb="select"] > div { min-height: 3.5rem; font-size: 1.1rem; }
[data-testid="stAlert"] { background: rgba(6, 182, 212, 0.1) !important; border: 1px solid rgba(6, 182, 212, 0.3); border-radius: 12px;}
[data-testid="stTextInput"] > div > div > input { font-size: 1.1rem; padding: 0.75rem;}

/* Watchlist heart animation */
@keyframes heartbeat {
  0% { transform: scale(1); }
  25% { transform: scale(1.1); }
  50% { transform: scale(1); }
  75% { transform: scale(1.1); }
  100% { transform: scale(1); }
}
.stButton > button[kind="primary"] p { display:flex; gap:0.5rem; align-items:center; justify-content:center; }
.stButton > button[kind="primary"]:hover p span { animation: heartbeat 1s ease-in-out infinite; }

/* Extra cinematic motion and spotlight UI */
.hero-shell {
    display: grid;
    grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
    gap: 1.5rem;
    align-items: stretch;
    margin-top: 0.75rem;
}
.hero-panel {
    position: relative;
    overflow: hidden;
    padding: 1.5rem 1.5rem 1.35rem;
    border-radius: 24px;
    background: linear-gradient(160deg, rgba(17,24,39,0.92), rgba(15,23,42,0.72));
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 20px 60px rgba(0,0,0,0.34);
    animation: fadeInUp 700ms ease both;
}
.hero-panel::before,
.hero-panel::after {
    content: "";
    position: absolute;
    inset: auto;
    border-radius: 999px;
    pointer-events: none;
    filter: blur(6px);
}
.hero-panel::before {
    width: 16rem;
    height: 16rem;
    top: -6rem;
    right: -2rem;
    background: radial-gradient(circle, rgba(6,182,212,0.2), transparent 68%);
}
.hero-panel::after {
    width: 12rem;
    height: 12rem;
    bottom: -4rem;
    left: -2rem;
    background: radial-gradient(circle, rgba(139,92,246,0.18), transparent 70%);
}
.hero-copy { position: relative; z-index: 1; }
.hero-badges { display: flex; flex-wrap: wrap; gap: 0.55rem; margin-top: 1rem; }
.hero-badge {
    display: inline-flex; align-items: center; gap: 0.45rem;
    padding: 0.45rem 0.8rem;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.1);
    background: rgba(255,255,255,0.04);
    color: #e2e8f0;
    font-size: 0.85rem;
    font-weight: 600;
}
.hero-stats {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
    margin-top: 1.1rem;
}
.stat-card {
    padding: 0.95rem 1rem;
    border-radius: 18px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.06);
}
.stat-card small {
    display: block;
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.35rem;
}
.stat-card strong {
    color: #fff;
    font-family: var(--font-display);
    font-size: 1.1rem;
}
.hero-spotlight {
    padding: 1.25rem;
    border-radius: 24px;
    background: linear-gradient(160deg, rgba(8,12,23,0.9), rgba(17,24,39,0.9));
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
    animation: fadeInUp 850ms ease both;
}
.section-kicker {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    margin: 2.25rem 0 0.9rem;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    color: #fff;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.03);
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
.spotlight-card {
    position: relative;
    border-radius: 18px;
    overflow: hidden;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    transition: transform 0.28s ease, box-shadow 0.28s ease;
    animation: fadeInUp 800ms ease both;
}
.spotlight-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 18px 40px rgba(0,0,0,0.38);
}
.spotlight-meta {
    padding: 0.85rem 0.85rem 1rem;
}
.spotlight-title {
    color: #fff;
    font-family: var(--font-display);
    font-size: 1.02rem;
    line-height: 1.2;
    margin-bottom: 0.35rem;
}
.spotlight-sub {
    color: var(--text-muted);
    font-size: 0.82rem;
    font-weight: 500;
}
.spotlight-card .poster-wrap {
    border-radius: 0;
    box-shadow: none;
}
.movie-card {
    position: relative;
    isolation: isolate;
    transform-style: preserve-3d;
    transition: transform 0.28s ease, box-shadow 0.28s ease;
}
.movie-card:hover {
  transform: perspective(1200px) rotateX(4deg) rotateY(-3deg) translateY(-8px);
}
.movie-card::before {
  content: "";
  position: absolute;
  inset: -1px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(6,182,212,0.16), rgba(139,92,246,0.12), transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: -1;
}
.movie-card:hover::before { opacity: 1; }
.poster-wrap {
  position: relative; aspect-ratio: 2/3; overflow: hidden; border-radius: 14px; background: #000;
  box-shadow: 0 10px 30px rgba(0,0,0,0.6), 0 14px 40px rgba(6,182,212,0.10);
  border: 1px solid rgba(255,255,255,0.12);
  transition: all 0.3s ease;
  transform-style: preserve-3d;
}
.movie-card:hover .poster-wrap {
  box-shadow: 0 20px 40px rgba(0,0,0,0.8), 0 0 0 2px rgba(6, 182, 212, 0.35);
  border-color: rgba(255,255,255,0.2);
  transform: translateZ(12px) scale(1.01);
}
.quote-card {
    width: min(100%, 1000px);
    padding: 2rem 2rem 1.5rem;
    border-radius: 28px;
    background: linear-gradient(135deg, rgba(17,24,39,0.9), rgba(15,23,42,0.75));
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 30px 70px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.08);
    position: relative;
    overflow: hidden;
    transform: perspective(1200px) rotateX(2deg);
}
.quote-card::before {
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at top right, rgba(6,182,212,0.18), transparent 30%),
                radial-gradient(circle at bottom left, rgba(139,92,246,0.2), transparent 25%);
}
.quote-mark {
    position: relative;
    z-index: 1;
    font-family: var(--font-display);
    font-size: 5.5rem;
    color: rgba(255,255,255,0.18);
    line-height: 1;
    margin-bottom: -1.2rem;
}
.quote-text {
    position: relative;
    z-index: 1;
    color: #fff;
    font-family: var(--font-display);
    font-size: clamp(2rem, 4vw, 4rem);
    line-height: 1.08;
    font-weight: 800;
    letter-spacing: -0.04em;
    margin: 0;
    text-shadow: 0 18px 32px rgba(0,0,0,0.18);
}
.quote-author {
    position: relative;
    z-index: 1;
    margin-top: 1rem;
    color: var(--text-muted);
    font-size: 0.95rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 700;
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
}
@media (max-width: 980px) {
    .hero-shell { grid-template-columns: 1fr; }
    .hero-stats { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
    .hero { padding-top: 1rem; }
    .hero h1 { font-size: 2.2rem; }
    .hero p { font-size: 1rem; }
    .section-title { font-size: 1.5rem; }
    .ticket-title { font-size: 2rem; }
    .quote-card { padding: 1.3rem 1.1rem 1rem; transform: none; }
    .quote-text { font-size: 1.6rem; }
    .quote-mark { font-size: 3.5rem; margin-bottom: -0.6rem; }
    .hero-panel, .hero-spotlight { padding: 1rem; border-radius: 20px; }
    .hero-badges { gap: 0.4rem; }
    .hero-badge { font-size: 0.78rem; padding: 0.4rem 0.7rem; }
    .hero-stats { gap: 0.55rem; }
    .stat-card { padding: 0.85rem 0.85rem; border-radius: 14px; }
    .stat-card strong { font-size: 0.98rem; }
    .section-kicker { margin-top: 1.5rem; font-size: 0.75rem; }
    .movie-card { margin-bottom: 1rem; }
    .spotlight-meta { padding: 0.75rem 0.7rem 0.9rem; }
    .spotlight-title { font-size: 0.95rem; }
    .spotlight-sub { font-size: 0.75rem; }
    .movie-link:hover .movie-card,
    .movie-link:focus-visible .movie-card {
        transform: translateY(-4px);
    }
    div[data-testid="stHorizontalBlock"] { gap: 0.75rem; }
    div[data-testid="column"] { min-width: 0 !important; }
    .stButton > button { min-height: 2.6rem; font-size: 0.9rem; }
}
</style>
"""


# ---------------------------------------------------------------------------
# 3. HELPER FUNCTIONS THAT BUILD HTML
# ---------------------------------------------------------------------------
def esc(text):
    """Make text safe to place inside HTML."""
    return html.escape(str(text))


def short_text(text, limit=130):
    """Cut a long text and add '...' at the end."""
    text = str(text)
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "..."


def genres_text(genres, limit=None):
    """'Sci-Fi|Drama|Adventure' -> 'Sci-Fi • Drama • Adventure'."""
    parts = [g for g in str(genres).split("|") if g]
    return " • ".join(parts[:limit] if limit else parts)


def year_text(movie):
    return str(movie["release_year"]) if movie["release_year"] > 0 else "-"


def rating_text(movie):
    return f"{movie['rating']:.1f}" if movie["rating"] > 0 else "N/A"


def movie_query_link(movie):
    """Build an internal link that opens the detail view for a movie."""
    return f"?movie={quote_plus(str(movie['title']))}"


def get_poster_source(movie):
    """Find a local poster picture for the movie, or return None if there is none."""
    for extension, mime in ((".jpg", "jpeg"), (".jpeg", "jpeg"), (".png", "png"), (".webp", "webp")):
        file = IMAGE_FOLDER / f"{movie['movie_id']}{extension}"
        if file.exists():
            data = base64.b64encode(file.read_bytes()).decode()
            return f"data:image/{mime};base64,{data}"
    return None


def poster_block(movie, overlay=False):
    """HTML for a movie poster. If the picture is missing, draw a modern gradient poster instead."""
    src = get_poster_source(movie)
    if src:
        inner = f'<img class="poster-img" src="{esc(src)}" alt="Poster of {esc(movie["title"])}">'
    else:
        first_genre = str(movie["genres"]).split("|")[0]
        hue = GENRE_HUE.get(first_genre, 200)
        icon = GENRE_ICON.get(first_genre, "🎬")
        inner = (f'<div class="poster-fallback" style="--h:{hue}">'
                 f'<div class="pf-icon">{icon}</div>'
                 f'<div class="pf-label">Poster of movie</div>'
                 f'<div class="pf-title">{esc(movie["title"])}</div>'
                 f'<div class="pf-bottom">{esc(year_text(movie))}</div></div>')
    if overlay:
        inner += f'<div class="overlay"><p>{esc(short_text(movie["overview"], 150))}</p></div>'
    return f'<div class="poster-wrap">{inner}</div>'


def platform_badges(streaming, big=False):
    """Coloured pill badges for every streaming platform. Handles missing information."""
    names = [p.strip() for p in str(streaming).split("|") if p.strip()]
    if not names:
        return '<span class="no-stream">No streaming info in our demo data</span>'
    size = " big" if big else ""
    return "".join(
        f'<span class="badge{size}"><span class="dot" style="background:{PLATFORM_COLORS.get(n, "#06b6d4")}; box-shadow:0 0 6px {PLATFORM_COLORS.get(n, "#06b6d4")}"></span>{esc(n)}</span>'
        for n in names)


def card_html(movie):
    """One movie-poster card: poster, title, year, rating, genre, platforms."""
    return "".join([
        f'<a class="movie-link" href="{movie_query_link(movie)}">',
        '<div class="movie-card">',
        poster_block(movie, overlay=True),
        f'<div class="card-title">{esc(movie["title"])}</div>',
        f'<div class="card-meta">{esc(year_text(movie))} &nbsp;<span style="color:var(--text-muted)">•</span>&nbsp; <span class="meta-rating">★ {rating_text(movie)}</span></div>',
        f'<div class="card-genre">{esc(genres_text(movie["genres"], limit=2))}</div>',
        f'<div class="card-where">{platform_badges(movie["streaming_platform"])}</div>',
        '</div></a>'])


def ticket_html(movie):
    """The big 'now showing' beautiful glassmorphic panel for the selected movie."""
    cast = ", ".join(str(movie["cast"]).split("|")[:4]) or "-"
    tags_html = "".join([f'<span class="ticket-tag">{esc(g.strip())}</span>' for g in str(movie["genres"]).split("|") if g.strip()])
    return "".join([
        '<div class="ticket">',
        f'<div class="ticket-poster">{poster_block(movie)}</div>',
        '<div class="ticket-body">',
        f'<div class="ticket-title">{esc(movie["title"])}</div>',
        f'<div class="ticket-line"><span>{esc(year_text(movie))}</span> <span>•</span> <span class="ticket-rating">★ {rating_text(movie)}</span>'
        f' <span>•</span> <span>{esc(movie["language"] or "-")}</span></div>',
        f'<div class="ticket-tags">{tags_html}</div>',
        f'<p class="ticket-overview">{esc(movie["overview"] or "No overview available.")}</p>',
        '<div class="stub">',
        f'<div><small>Director</small><span>{esc(movie["director"] or "-")}</span></div>',
        f'<div><small>Cast</small><span>{esc(cast)}</span></div>',
        '</div></div></div>'])


# ---------------------------------------------------------------------------
# 4. WATCHLIST  (kept in st.session_state - no database, no login)
# ---------------------------------------------------------------------------
def toggle_watchlist(title):
    """Add the movie to the watchlist, or remove it if it is already there."""
    if title in st.session_state.watchlist:
        st.session_state.watchlist.remove(title)
        st.session_state.flash = f"Removed '{title}' from your playlist."
    else:
        st.session_state.watchlist.append(title)
        st.session_state.flash = f"Added '{title}' to your playlist."


def watchlist_button(title, key):
    """A button that adds/removes one movie. The page reloads after a click."""
    saved = title in st.session_state.watchlist
    label = "♥ In your playlist (click to remove)" if saved else "♡ Add to Playlist"
    if st.button(label, key=key, type="secondary" if saved else "primary"):
        toggle_watchlist(title)
        st.rerun()


# ---------------------------------------------------------------------------
# 5. THE PAGE
# ---------------------------------------------------------------------------
st.markdown(CSS, unsafe_allow_html=True)

movies = get_movies()
if movies.empty:
    st.error("Our film vault is empty. Please check that movie_data.csv is in the project folder and has rows.")
    st.stop()

requested_movie = st.query_params.get("movie")
if isinstance(requested_movie, list):
    requested_movie = requested_movie[0] if requested_movie else None
if requested_movie:
    match = movies[movies["title"].str.lower() == str(requested_movie).strip().lower()]
    if not match.empty:
        st.session_state.selected_movie = match.iloc[0]["title"]

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []
if "core_genre" not in st.session_state:
    st.session_state.core_genre = None
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None
if "selected_genre" not in st.session_state:
    st.session_state.selected_genre = "All"
if "show_recommendations" not in st.session_state:
    st.session_state.show_recommendations = False
if "classic_visible_count" not in st.session_state:
    st.session_state.classic_visible_count = 8
if "movie_order_seed" not in st.session_state:
    st.session_state.movie_order_seed = random.randint(1, 999999)
if "quote_seed" not in st.session_state:
    st.session_state.quote_seed = int(time.time() // 5)
if "flash" in st.session_state:                       # small message after a watchlist click
    st.toast(st.session_state.pop("flash"), icon="🎞️")

all_titles = sorted(movies["title"].tolist())


def find_movie(title):
    """Return the row of the movie with this title, or None if it does not exist."""
    rows = movies[movies["title"] == title]
    return None if rows.empty else rows.iloc[0]


def render_grid(df, prefix, per_row=4, show_remove=False):
    """Show movies as poster cards, `per_row` cards in each row."""
    if df.empty:
        st.info("No movies to show here yet.")
        return
    for start in range(0, len(df), per_row):
        columns = st.columns(per_row)
        for column, (_, movie) in zip(columns, df.iloc[start:start + per_row].iterrows()):
            with column:
                st.markdown(card_html(movie), unsafe_allow_html=True)
                if show_remove and st.button("✕ Remove", key=f"{prefix}_remove_{movie['movie_id']}"):
                    toggle_watchlist(movie["title"])
                    st.rerun()


def section(title, subtitle=""):
    """Print a section heading."""
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="section-sub">{subtitle}</p>', unsafe_allow_html=True)


def render_genre_controls(selected_genre):
    """Render genre buttons in rows so they stay usable on small screens."""
    for row_index in range(0, len(GENRE_BUTTONS), 4):
        row = GENRE_BUTTONS[row_index:row_index + 4]
        columns = st.columns(len(row))
        for column, (emoji, genre) in zip(columns, row):
            with column:
                is_selected = selected_genre == genre
                button_label = f"{emoji} {genre}"
                button_key = f"home_genre_{row_index}_{genre.lower().replace(' ', '_').replace('-', '_')}"
                if st.button(button_label, key=button_key, type="primary" if is_selected else "secondary"):
                    st.session_state.classic_visible_count = 8
                    st.session_state.selected_genre = "All" if is_selected else genre
                    st.rerun()


def spotlight_html(movie):
    """Compact poster card used in the hero spotlight row."""
    return "".join([
        f'<a class="movie-link" href="{movie_query_link(movie)}">',
        '<div class="spotlight-card">',
        poster_block(movie),
        '<div class="spotlight-meta">',
        f'<div class="spotlight-title">{esc(movie["title"])}</div>',
        f'<div class="spotlight-sub">{esc(year_text(movie))} • ★ {rating_text(movie)}</div>',
        '</div></div></a>',
    ])

# ----- THE PAGE -------------------------------------------------------------
# SCENE 1: Genre Selection Flow
if not st.session_state.selected_movie:
    classic_movies = movies[movies["release_year"] <= 2000].sort_values(["rating", "release_year"], ascending=[False, False])
    if classic_movies.empty:
        classic_movies = movies.sort_values(["rating", "release_year"], ascending=[False, False]).head(12)

    ranked_movies = classic_movies.copy()
    if not ranked_movies.empty:
        random.seed(st.session_state.movie_order_seed)
        ranked_movies = ranked_movies.sample(frac=1, random_state=st.session_state.movie_order_seed).reset_index(drop=True)
    else:
        ranked_movies = classic_movies

    quotes = [
        ("The whole of cinema is a dream; the projector is the dream-maker.", "— Abbas Kiarostami"),
        ("Movies are like memories: they stay with us long after the scene is gone.", "— Martin Scorsese"),
        ("A good film is a journey that makes you feel more alive.", "— Orson Welles"),
        ("Cinema should be a window to another world, not a mirror of the same.", "— Akira Kurosawa"),
        ("Every frame tells a story, and every story changes the way we see.", "— Federico Fellini"),
        ("The best kind of movie is the one that leaves you thinking when it ends.", "— Ingmar Bergman"),
        ("Film is the art of time, and time is the art of memory.", "— Chris Marker"),
        ("A film is never really about what it is about. It is about how it makes you feel.", "— David Lynch"),
        ("You can’t make a great movie just by following a formula. You need a pulse.", "— Quentin Tarantino"),
        ("The magic of cinema is that it can turn silence into a world of emotion.", "— Wong Kar-wai"),
        ("Every great film is a question that keeps echoing after the credits roll.", "— Stanley Kubrick"),
        ("There is no greater joy than discovering a film that feels like a secret.", "— Sofia Coppola"),
        ("If a movie makes you feel, it has already won the first round.", "— Pedro Almodóvar"),
        ("The screen is a door. Cinema opens it and invites us in.", "— Alfonso Cuarón"),
        ("A scene can be a poem if the camera listens closely enough.", "— Claire Denis"),
        ("Some films don’t just entertain us. They rearrange the way we think.", "— Denis Villeneuve"),
        ("The best stories are the ones we feel in our chest more than in our head.", "— Paul Thomas Anderson"),
        ("Not every movie needs an answer. Some just need a mood.", "— Richard Linklater"),
        ("To watch a film is to spend time inside another human’s imagination.", "— Werner Herzog"),
        ("Cinema gives us windows, mirrors, and doors all at once.", "— Bong Joon-ho"),
        ("The most powerful shots are the ones that stay with you long after the movie is over.", "— Roger Deakins"),
        ("A masterpiece is not always loud. Sometimes it whispers and changes your life.", "— Terrence Malick"),
        ("The purpose of a movie is not only to entertain, but to awaken.", "— Spike Lee"),
        ("A film can be a memory machine and a dream machine at the same time.", "— Tsai Ming-liang"),
        ("The cinema of the future is still built in the same way: with wonder.", "— Greta Gerwig"),
        ("You don't just watch a movie. You enter it.", "— Christopher Nolan"),
        ("There are films that become part of you. That is the true cinema magic.", "— James Cameron"),
    ]
    now = int(time.time())
    seed = now // 30
    quote_text, quote_author = quotes[seed % len(quotes)]

    st.markdown(
        f'''
        <div class="quote-shell">
            <div class="quote-card">
                <div class="quote-mark">“</div>
                <div class="quote-text">{esc(quote_text)}</div>
                <div class="quote-author">{esc(quote_author)}</div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-kicker">Choose a mood</div>', unsafe_allow_html=True)
    if st.button("All", key="home_genre_all", type="primary" if st.session_state.selected_genre == "All" else "secondary"):
        st.session_state.classic_visible_count = 8
        st.session_state.selected_genre = "All"
        st.rerun()
    render_genre_controls(st.session_state.selected_genre)

    selected_genre = st.session_state.selected_genre
    if selected_genre == "All":
        filtered_classics = ranked_movies
        section("Classic cinema", "The greatest stories, the iconic faces, the unforgettable frames.")
    else:
        filtered_classics = ranked_movies[ranked_movies["genres"].apply(lambda g: selected_genre in str(g).split("|"))]
        section(f"Classic {selected_genre} picks", "Timeless films and unforgettable visuals.")

    if filtered_classics.empty:
        st.info("No classic picks match right now.")
    else:
        visible_movies = filtered_classics.head(st.session_state.classic_visible_count)
        render_grid(visible_movies, prefix="classic_home", per_row=4)

        if st.session_state.classic_visible_count < len(filtered_classics):
            if st.button("More movies", key="more_classic_movies", type="primary"):
                st.session_state.classic_visible_count += 8
                st.rerun()

# SCENE 2: Movie Detail Flow
else:
    selected = find_movie(st.session_state.selected_movie)
    if selected is None:
        st.session_state.selected_movie = None
        st.rerun()

    if st.button("← Back to classics", key="back_btn"):
        st.session_state.selected_movie = None
        st.session_state.show_recommendations = False
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()

    st.markdown(ticket_html(selected), unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(
            '<div class="ticket-line"><span>Available on:</span> &nbsp; ' + platform_badges(selected["streaming_platform"], big=True) + '</div>',
            unsafe_allow_html=True,
        )
    with col2:
        watchlist_button(selected["title"], key="detail_watchlist")

    st.markdown(f'<div class="demo-note">{DEMO_NOTE}</div>', unsafe_allow_html=True)
    st.markdown("<hr style='border-color:rgba(255,255,255,0.05); margin:3rem 0;'>", unsafe_allow_html=True)

    if st.button("Predict movies like this", key="generate_recommendations", type="primary"):
        st.session_state.show_recommendations = True

    if st.session_state.get("show_recommendations"):
        section("If you like this, you would also love...", f"Machine-learning predictions inspired by {esc(selected['title'])}.")
        all_similar = predict(selected["title"], n=8)
        if all_similar.empty:
            st.info("No similar films found in our vault.")
        else:
            render_grid(all_similar, prefix="similar_movies", per_row=4)

st.markdown("<br><br>", unsafe_allow_html=True)
section("My Playlist", "Saved movies stay here so you can come back to them later.")
playlist_cols = st.columns([1, 3])
with playlist_cols[0]:
    if st.session_state.watchlist and st.button("Clear playlist", key="clear_playlist", type="secondary"):
        st.session_state.watchlist = []
        st.session_state.flash = "Playlist cleared."
        st.rerun()
with playlist_cols[1]:
    if st.session_state.watchlist:
        st.caption(f"{len(st.session_state.watchlist)} movie(s) saved")

if not st.session_state.watchlist:
    st.info("Your playlist is empty. Click ♡ Add to Playlist on any film to save it here.")
else:
    saved_titles = [title for title in st.session_state.watchlist if title in set(movies["title"].tolist())]
    saved_movies = movies.set_index("title").loc[saved_titles].reset_index()
    render_grid(saved_movies, prefix="saved", per_row=4, show_remove=True)

st.markdown('<div class="footer">cinematch by rudra-hue<br>For the classics, the deep cuts, and the next obsession.</div>', unsafe_allow_html=True)

