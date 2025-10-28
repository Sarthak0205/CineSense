import os
import json
import requests
import pandas as pd
from tqdm import tqdm

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_URL = "https://api.themoviedb.org/3/search/multi"
DATA_PATH = "data/final_dataset_clustered.csv"
CACHE_PATH = "data/poster_cache.json"

df = pd.read_csv(DATA_PATH)
titles = df["title"].dropna().unique().tolist()

if os.path.exists(CACHE_PATH):
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        cache = json.load(f)
else:
    cache = {}

def fetch_poster(title):
    if title.lower() in cache:
        return cache[title.lower()]

    try:
        res = requests.get(TMDB_URL, params={"api_key": TMDB_API_KEY, "query": title}, timeout=6)
        data = res.json()
        if data.get("results"):
            poster_path = data["results"][0].get("poster_path")
            if poster_path:
                url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                cache[title.lower()] = url
                return url
    except Exception:
        pass
    cache[title.lower()] = None
    return None

print(f"📦 Prefetching posters for {len(titles)} titles...")
for t in tqdm(titles[:1000]):  # you can increase this limit later
    fetch_poster(t)

with open(CACHE_PATH, "w", encoding="utf-8") as f:
    json.dump(cache, f, indent=2)

print(f"✅ Poster cache saved to {CACHE_PATH}")
