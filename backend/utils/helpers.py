import os
import json
import re
import time
import requests
from requests.adapters import HTTPAdapter, Retry

# ======================================================
# 🔹 API Keys & Config
# ======================================================
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "YOUR_TMDB_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "YOUR_OMDB_API_KEY")
CACHE_FILE = "data/poster_cache.json"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# ======================================================
# 🔹 Setup requests session with retry mechanism
# ======================================================
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
session.mount("https://", HTTPAdapter(max_retries=retries))

# ======================================================
# 🔹 Cache setup
# ======================================================
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            poster_cache = json.load(f)
        print(f"🧠 Loaded {len(poster_cache)} cached posters.")
    except Exception:
        poster_cache = {}
        print("⚠️ Poster cache corrupted, starting fresh.")
else:
    poster_cache = {}
    print("🆕 No poster cache found — starting fresh.")

# ======================================================
# 🔹 Utility functions
# ======================================================
def normalize_title(title: str) -> str:
    """Clean and normalize title for better API search matching."""
    title = re.sub(r"[:\-–_]+", " ", title)  # replace symbols with spaces
    title = re.sub(r"\(.*?\)", "", title)     # remove parentheses text
    title = re.sub(r"\s+", " ", title).strip()
    return title


# ======================================================
# 🔹 Fetch from TMDB
# ======================================================
def fetch_tmdb_poster(title, content_type):
    try:
        tmdb_type = "movie" if content_type.lower() == "movie" else "tv"
        params = {"api_key": TMDB_API_KEY, "query": title}
        response = session.get(f"{TMDB_BASE_URL}/search/{tmdb_type}", params=params, timeout=8)
        data = response.json().get("results", [])
        if data and data[0].get("poster_path"):
            return f"https://image.tmdb.org/t/p/w500{data[0]['poster_path']}"
    except Exception as e:
        print(f"⚠️ TMDB fetch error for {title}: {e}")
    return None


# ======================================================
# 🔹 Fetch from Jikan (Anime API)
# ======================================================
def fetch_jikan_poster(title):
    try:
        url = f"https://api.jikan.moe/v4/anime?q={title}&limit=1"
        res = session.get(url, timeout=8).json()
        if "data" in res and len(res["data"]) > 0:
            return res["data"][0]["images"]["jpg"]["large_image_url"]
    except Exception as e:
        print(f"⚠️ Jikan fetch error for {title}: {e}")
    return None


# ======================================================
# 🔹 Fetch from OMDb (Backup Source)
# ======================================================
def fetch_omdb_poster(title):
    try:
        if not OMDB_API_KEY or OMDB_API_KEY == "YOUR_OMDB_API_KEY":
            return None
        url = f"https://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
        res = session.get(url, timeout=8).json()
        if res.get("Poster") and res["Poster"] != "N/A":
            return res["Poster"]
    except Exception as e:
        print(f"⚠️ OMDb fetch error for {title}: {e}")
    return None


# ======================================================
# 🔹 Main function: get_poster_url()
# ======================================================
def get_poster_url(title, content_type):
    """Fetch and cache poster URLs using multiple APIs with fallback."""
    if not title:
        return "https://via.placeholder.com/500x750?text=No+Title"

    title = normalize_title(title)
    content_type = content_type.lower().strip()
    key = f"{content_type}::{title.lower()}"

    # ✅ Return from cache if exists
    if key in poster_cache:
        return poster_cache[key]

    poster_url = None

    # 1️⃣ Jikan for Anime
    if content_type == "anime":
        poster_url = fetch_jikan_poster(title)
        if not poster_url:
            alt_title = title.replace("Season", "").replace("Part", "").strip()
            poster_url = fetch_jikan_poster(alt_title)

    # 2️⃣ TMDB for Movies & Series
    if not poster_url:
        poster_url = fetch_tmdb_poster(title, content_type)
        if not poster_url:
            alt_title = title.split(":")[0].split("-")[0].strip()
            poster_url = fetch_tmdb_poster(alt_title, content_type)

    # 3️⃣ OMDb Backup (Movies/Series only)
    if not poster_url and content_type != "anime":
        poster_url = fetch_omdb_poster(title)

    # 4️⃣ Final Static Fallback
    if not poster_url:
        if content_type == "anime":
            poster_url = "/posters/anime_default.jpg"
        elif content_type == "series":
            poster_url = "/posters/series_default.jpg"
        else:
            poster_url = "/posters/movie_default.jpg"

    # ✅ Cache and save
    poster_cache[key] = poster_url
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(poster_cache, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to write poster cache: {e}")

    return poster_url
