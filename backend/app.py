import os
import re
import time
import threading
import requests
from urllib.parse import quote
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from hybrid_recommender import HybridRecommender
import hashlib

# ───────────────────────────────
# 🔹 Cache Setup
# ───────────────────────────────
CACHE_DIR = "cache/posters"
os.makedirs(CACHE_DIR, exist_ok=True)
MAX_CACHE_FILES = 300  # Keep at most 300 posters

# ───────────────────────────────
# 🔹 Setup Flask App
# ───────────────────────────────
load_dotenv()
app = Flask(__name__)
CORS(app)

print("🚀 Initializing CineSense Model...")
model = HybridRecommender()
print("✅ Model ready!")

# ───────────────────────────────
# 🔑 API Keys + URLs
# ───────────────────────────────
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()
if not TMDB_API_KEY:
    raise ValueError("❌ Missing TMDB_API_KEY in .env")

TMDB_MOVIE_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_TV_URL = "https://api.themoviedb.org/3/search/tv"
TMDB_MULTI_URL = "https://api.themoviedb.org/3/search/multi"
JIKAN_URL = "https://api.jikan.moe/v4/anime"

# ───────────────────────────────
# 🧠 Request Session + Cache
# ───────────────────────────────
session = requests.Session()
session.headers.update({"Accept": "application/json"})
cache_lock = threading.Lock()
metadata_cache = {}

# ───────────────────────────────
# 🧰 Helper Functions
# ───────────────────────────────
def get_cache_path(title):
    """Return a unique cache file path for a given title."""
    safe_name = hashlib.md5(title.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{safe_name}.jpg")

def manage_cache_size():
    """Ensure cache folder doesn't exceed MAX_CACHE_FILES."""
    files = sorted(
        [(f, os.path.getmtime(os.path.join(CACHE_DIR, f))) for f in os.listdir(CACHE_DIR)],
        key=lambda x: x[1]
    )
    if len(files) > MAX_CACHE_FILES:
        to_delete = files[:len(files) - MAX_CACHE_FILES]
        for f, _ in to_delete:
            os.remove(os.path.join(CACHE_DIR, f))

def safe_tmdb_fetch(endpoint, params, retries=3):
    """Safely fetch from TMDB with retries and exponential backoff."""
    for attempt in range(retries):
        try:
            time.sleep(0.3)  # prevent hitting TMDB too fast
            resp = session.get(endpoint, params=params, timeout=8)
            if resp.status_code == 200:
                return resp.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ TMDB fetch attempt {attempt+1} failed: {e}")
            time.sleep(1.5 * (attempt + 1))
    return {}

# ───────────────────────────────
# 🎬 Fetch Metadata (TMDB / Jikan)
# ───────────────────────────────
def fetch_metadata(title, content_type="movie"):
    """Fetch poster, rating, and overview from TMDB or Jikan (cached for speed)."""
    with cache_lock:
        if title in metadata_cache:
            return metadata_cache[title]

    clean_title = re.sub(r"[^\w\s:]", "", title).strip()
    fallback = {
        "title": title,
        "poster": "https://via.placeholder.com/500x750?text=No+Image",
        "rating": 0,
        "overview": "No overview available.",
        "release_date": "N/A",
    }

    # 🎬 Try TMDB for movies & series
    try:
        endpoint = TMDB_MOVIE_URL if content_type == "movie" else TMDB_TV_URL
        params = {"api_key": TMDB_API_KEY, "query": clean_title, "language": "en-US"}

        data = safe_tmdb_fetch(endpoint, params)
        if not data.get("results"):
            # Try multi-search fallback
            data = safe_tmdb_fetch(TMDB_MULTI_URL, params)

        if data.get("results"):
            best = next((r for r in data["results"] if r.get("poster_path")), data["results"][0])
            poster_url = f"https://image.tmdb.org/t/p/w500{best.get('poster_path')}" if best.get("poster_path") else fallback["poster"]

            result = {
                "title": best.get("title") or best.get("name") or title,
                "poster": poster_url,
                "rating": best.get("vote_average", 0),
                "overview": best.get("overview", fallback["overview"]),
                "release_date": best.get("release_date") or best.get("first_air_date") or "N/A",
            }

            # Cache poster locally
            try:
                img_data = session.get(poster_url, timeout=8).content
                with open(get_cache_path(title), "wb") as f:
                    f.write(img_data)
                manage_cache_size()
            except Exception as e:
                print(f"⚠️ Failed to cache poster for '{title}': {e}")

            with cache_lock:
                metadata_cache[title] = result
            return result

    except Exception as e:
        print(f"⚠️ TMDB fetch failed for '{title}': {e}")

    # 🎌 Fallback for Anime via Jikan
    if content_type == "anime":
        try:
            jikan_resp = session.get(f"{JIKAN_URL}?q={quote(clean_title)}&limit=1", timeout=8)
            data = jikan_resp.json()
            if data.get("data"):
                anime = data["data"][0]
                poster_url = anime.get("images", {}).get("jpg", {}).get("large_image_url", fallback["poster"])
                result = {
                    "title": anime.get("title_english") or anime.get("title") or title,
                    "poster": poster_url,
                    "rating": anime.get("score", 0),
                    "overview": anime.get("synopsis", fallback["overview"]),
                    "release_date": anime.get("aired", {}).get("from", "N/A"),
                }

                # Cache anime poster locally
                try:
                    img_data = session.get(poster_url, timeout=8).content
                    with open(get_cache_path(title), "wb") as f:
                        f.write(img_data)
                    manage_cache_size()
                except Exception as e:
                    print(f"⚠️ Failed to cache anime poster for '{title}': {e}")

                with cache_lock:
                    metadata_cache[title] = result
                return result
        except Exception as e:
            print(f"⚠️ Jikan fetch failed for '{title}': {e}")

    with cache_lock:
        metadata_cache[title] = fallback
    return fallback

# ───────────────────────────────
# 🎯 Recommendation Endpoint
# ───────────────────────────────
@app.route("/api/recommend", methods=["POST"])
def recommend():
    try:
        data = request.get_json()
        title = data.get("title", "").strip()
        content_type = data.get("type", "").strip().lower()

        if not title:
            return jsonify({"error": "Missing title"}), 400

        print(f"\n🎯 Request → Title: {title}, Type: {content_type}")

        # 🧠 Get recommendations
        recs = model.recommend(title, content_type, top_n=10)

        # If title not in dataset → use TMDB/Jikan direct search fallback
        if recs is None or isinstance(recs, list) and not recs:
            print(f"⚠️ Title '{title}' not found in dataset.")
            meta = fetch_metadata(title, content_type)
            return jsonify({
                "error": f"'{title}' not found in dataset.",
                "suggestion": "Try another similar title.",
                "fallback": meta
            }), 200

        # Handle DataFrame vs List
        if isinstance(recs, list):
            titles = recs
        else:
            titles = recs["title"].tolist()

        print(f"📦 Raw recommendations: {titles}")

        # 🎞️ Enrich with metadata
        enriched = [fetch_metadata(t, content_type) for t in titles[:10]]

        print(f"✅ Returning {len(enriched)} enriched recommendations\n")
        return jsonify(enriched)

    except Exception as e:
        print(f"❌ Recommendation error: {e}")
        return jsonify({"error": str(e)}), 500

# ───────────────────────────────
# 🚀 Run Server
# ───────────────────────────────
if __name__ == "__main__":
    print("🔹 Starting CineSense backend server...")
    app.run(debug=True, threaded=True)
