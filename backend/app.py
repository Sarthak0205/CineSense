import os
import time
import threading
import hashlib
import requests
from urllib.parse import quote
from flask import Flask, request, jsonify, send_from_directory, Response
from dotenv import load_dotenv
from flask_cors import CORS
from hybrid_recommender import HybridRecommender

load_dotenv()
app = Flask(__name__, static_folder=None)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

DATA_DIR = os.getenv("DATA_DIR", "data")
POSTER_CACHE = os.path.join(DATA_DIR, "posters_cache")
os.makedirs(POSTER_CACHE, exist_ok=True)
MAX_CACHE_FILES = int(os.getenv("MAX_CACHE_FILES", 400))

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()
if not TMDB_API_KEY:
    print("⚠️ Warning: TMDB_API_KEY not set in .env — TMDB poster fetches will fail (Jikan/fallback used).")

TMDB_SEARCH_MOVIE = "https://api.themoviedb.org/3/search/movie"
TMDB_SEARCH_TV = "https://api.themoviedb.org/3/search/tv"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
JIKAN_SEARCH = "https://api.jikan.moe/v4/anime"

session = requests.Session()
session.headers.update({"Accept": "application/json", "User-Agent": "CineSense/1.0"})
cache_lock = threading.Lock()
metadata_cache = {}  # in-memory metadata cache

recommender = HybridRecommender(
    dataset_path=os.getenv("DATASET_PATH", os.path.join(DATA_DIR, "final_dataset.csv")),
    embeddings_path=os.getenv("EMBEDDINGS_PATH", os.path.join(DATA_DIR, "embeddings.npy")),
    clusters_path=os.getenv("CLUSTERS_PATH", os.path.join(DATA_DIR, "kmeans.pkl")),
    n_clusters=int(os.getenv("N_CLUSTERS", 25)),
    recompute=False
)

def _cache_filename(title):
    h = hashlib.md5(title.encode("utf-8")).hexdigest()
    return os.path.join(POSTER_CACHE, f"{h}.jpg")

def _manage_cache_size():
    files = sorted(
        [os.path.join(POSTER_CACHE, f) for f in os.listdir(POSTER_CACHE)],
        key=lambda p: os.path.getmtime(p)
    )
    if len(files) > MAX_CACHE_FILES:
        for f in files[:len(files) - MAX_CACHE_FILES]:
            try:
                os.remove(f)
            except Exception:
                pass

@app.route("/poster/<filename>")
def poster_serve(filename):
    return send_from_directory(POSTER_CACHE, filename)

def fetch_metadata(title, content_type="movie", max_tmdb_attempts=2):
    key = f"{title}__{content_type}"
    with cache_lock:
        if key in metadata_cache:
            return metadata_cache[key]
    
    cached_path = _cache_filename(title)
    if os.path.exists(cached_path):
        poster_url = f"/poster/{os.path.basename(cached_path)}"
    else:
        poster_url = None
    
    fallback = {
        "title": title,
        "poster": poster_url or "https://via.placeholder.com/500x750?text=No+Image",
        "rating": 0.0,
        "overview": "No overview available.",
        "release_date": "N/A",
        "source": "fallback"
    }
    
    # TMDB for movies and series
    if TMDB_API_KEY and content_type in ("movie", "movies", "series", "tv"):
        endpoint = TMDB_SEARCH_MOVIE if "movie" in content_type else TMDB_SEARCH_TV
        params = {"api_key": TMDB_API_KEY, "query": title, "language": "en-US", "page": 1}
        for attempt in range(max_tmdb_attempts):
            try:
                r = session.get(endpoint, params=params, timeout=5)
                r.raise_for_status()
                data = r.json()
                if data.get("results"):
                    best = next((x for x in data["results"] if x.get("poster_path")), data["results"][0])
                    poster_path = best.get("poster_path") or best.get("backdrop_path")
                    if poster_path:
                        poster_full = TMDB_IMAGE_BASE + poster_path
                        try:
                            img = session.get(poster_full, timeout=6).content
                            with open(cached_path, "wb") as fh:
                                fh.write(img)
                            _manage_cache_size()
                            poster_url = f"/poster/{os.path.basename(cached_path)}"
                        except Exception:
                            poster_url = poster_full
                    result = {
                        "title": best.get("title") or best.get("name") or title,
                        "poster": poster_url or fallback["poster"],
                        "rating": float(best.get("vote_average") or 0.0),
                        "overview": best.get("overview") or fallback["overview"],
                        "release_date": best.get("release_date") or best.get("first_air_date") or "N/A",
                        "source": "tmdb"
                    }
                    with cache_lock:
                        metadata_cache[key] = result
                    return result
                else:
                    break
            except requests.RequestException as e:
                print(f"⚠️ TMDB fetch {attempt+1} failed for '{title}': {e}")
                time.sleep(0.6)
    
    # Jikan for anime
    if content_type == "anime":
        try:
            url = f"{JIKAN_SEARCH}?q={quote(title)}&limit=1"
            r = session.get(url, timeout=6)
            data = r.json()
            if data.get("data"):
                anime = data["data"][0]
                poster_url_candidate = anime.get("images", {}).get("jpg", {}).get("large_image_url")
                if poster_url_candidate:
                    try:
                        img = session.get(poster_url_candidate, timeout=6).content
                        with open(cached_path, "wb") as fh:
                            fh.write(img)
                        _manage_cache_size()
                        poster_url = f"/poster/{os.path.basename(cached_path)}"
                    except Exception:
                        poster_url = poster_url_candidate
                result = {
                    "title": anime.get("title_english") or anime.get("title") or title,
                    "poster": poster_url or fallback["poster"],
                    "rating": float(anime.get("score") or 0.0),
                    "overview": anime.get("synopsis") or fallback["overview"],
                    "release_date": (anime.get("aired", {}).get("from") or "N/A")[:10],
                    "source": "jikan"
                }
                with cache_lock:
                    metadata_cache[key] = result
                return result
        except Exception as e:
            print(f"⚠️ Jikan fetch failed for '{title}': {e}")
    
    # Fallback: TMDB multi-search
    if TMDB_API_KEY:
        try:
            endpoint = "https://api.themoviedb.org/3/search/multi"
            params = {"api_key": TMDB_API_KEY, "query": title, "language": "en-US", "page": 1}
            r = session.get(endpoint, params=params, timeout=5)
            data = r.json()
            if data.get("results"):
                best = next((x for x in data["results"] if x.get("poster_path")), data["results"][0])
                poster_path = best.get("poster_path")
                poster_full = TMDB_IMAGE_BASE + poster_path if poster_path else None
                if poster_full:
                    try:
                        img = session.get(poster_full, timeout=6).content
                        with open(cached_path, "wb") as fh:
                            fh.write(img)
                        _manage_cache_size()
                        poster_url = f"/poster/{os.path.basename(cached_path)}"
                    except Exception:
                        poster_url = poster_full
                result = {
                    "title": best.get("title") or best.get("name") or title,
                    "poster": poster_url or fallback["poster"],
                    "rating": float(best.get("vote_average") or 0.0),
                    "overview": best.get("overview") or fallback["overview"],
                    "release_date": best.get("release_date") or best.get("first_air_date") or "N/A",
                    "source": "tmdb_multi"
                }
                with cache_lock:
                    metadata_cache[key] = result
                return result
        except Exception:
            pass
    
    with cache_lock:
        metadata_cache[key] = fallback
    return fallback

@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    payload = request.get_json() or {}
    title = str(payload.get("title", "")).strip()
    c_type = str(payload.get("type", "")).strip().lower()
    top_n = int(payload.get("top_n", 10))
    
    print(f"\n🔍 Recommendation request: title='{title}', type='{c_type}', top_n={top_n}")
    
    if not title:
        return jsonify({"error": "Missing 'title' in request body."}), 400
    
    try:
        recs_df = recommender.recommend(title, content_type=c_type or "movie", top_n=top_n)
        
        if recs_df is None or len(recs_df) == 0:
            print(f"⚠️ No recommendations found for '{title}'")
            meta = fetch_metadata(title, content_type=c_type or "movie")
            return jsonify({
                "error": f"Title '{title}' not found in dataset.",
                "results": [],
                "fallback": meta
            }), 200
        
        print(f"✅ Found {len(recs_df)} recommendations")
        enriched = []
        
        for i in range(len(recs_df)):
            row = recs_df.iloc[i]
            t = str(row.get("title", ""))
            
            # Fetch metadata
            meta = fetch_metadata(t, content_type=c_type or "movie")
            
            # Build result with safe type conversions
            result = {
                "id": i + 1,  # Add unique ID for React key
                "title": meta.get("title", t),
                "poster": meta.get("poster", "https://via.placeholder.com/500x750?text=No+Image"),
                "rating": float(meta.get("rating", 0)),
                "overview": meta.get("overview", "No overview available."),
                "release_date": meta.get("release_date", "N/A"),
                "source": str(meta.get("source", "unknown")),
                # Additional fields from recommender
                "genre": str(row.get("genre", "")),
                "similarity": float(row.get("similarity", 0)),
                "final_score": float(row.get("final_score", 0)),
                "type": str(row.get("type", "")),
                "cluster": int(row.get("cluster", -1)),
                "year": int(row.get("year", 0))
            }
            enriched.append(result)
            print(f"  → {i+1}. {result['title']} (score: {result['final_score']:.3f})")
        
        print(f"✅ Returning {len(enriched)} enriched recommendations\n")
        return jsonify({"query": title, "results": enriched}), 200
        
    except Exception as e:
        import traceback
        print("❌ Recommendation error:", e)
        print(traceback.format_exc())
        return jsonify({"error": str(e), "results": []}), 500

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model_ready": True}), 200

@app.route("/api/test", methods=["GET"])
def test():
    """Test endpoint to verify backend is working"""
    return jsonify({
        "status": "ok",
        "message": "Backend is running",
        "sample_recommendation": {
            "id": 1,
            "title": "Test Movie",
            "poster": "https://via.placeholder.com/500x750?text=Test+Movie",
            "rating": 8.5,
            "overview": "This is a test movie to verify the API structure.",
            "release_date": "2024-01-01",
            "source": "test",
            "genre": "Action, Adventure",
            "similarity": 0.95,
            "final_score": 0.89,
            "type": "movie",
            "cluster": 5,
            "year": 2024
        }
    }), 200

# Handle OPTIONS for CORS
@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

if __name__ == "__main__":
    print("🔹 Starting CineSense backend server...")
    print(f"📂 Data directory: {DATA_DIR}")
    print(f"🎬 TMDB API: {'✅ Configured' if TMDB_API_KEY else '❌ Not configured'}")
    print(f"🖼️ Poster cache: {POSTER_CACHE}")
    print(f"🚀 Server starting on http://0.0.0.0:{os.getenv('PORT', 5000)}\n")
    app.run(debug=True, threaded=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))