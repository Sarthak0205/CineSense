import pandas as pd, requests, concurrent.futures, time, json

TMDB_KEY = "YOUR_TMDB_KEY"  # 🔑 replace with your actual key
INPUT_PATH = "data/final_dataset_verified.csv"
OUTPUT_PATH = "data/final_dataset_realyears_fast.csv"

# --- API FETCHERS ---

def fetch_tmdb_year(title):
    """Fetch release year from TMDB (movie/tv)."""
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_KEY}&query={title}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return None
        data = r.json().get("results", [])
        if not data: return None
        item = data[0]
        for key in ["release_date", "first_air_date"]:
            if key in item and item[key]:
                return int(item[key][:4])
    except Exception:
        return None
    return None


def fetch_anilist_year(title):
    """Fetch release year from AniList GraphQL API."""
    query = '''
    query ($search: String) {
      Media(search: $search, type: ANIME) {
        startDate { year }
      }
    }'''
    try:
        r = requests.post(
            "https://graphql.anilist.co",
            json={"query": query, "variables": {"search": title}},
            timeout=5
        )
        if r.status_code != 200: return None
        data = r.json().get("data", {}).get("Media", {})
        return data.get("startDate", {}).get("year")
    except Exception:
        return None


# --- PARALLEL FETCHING LOGIC ---

def fetch_year(row):
    """Try TMDB first, then AniList."""
    title = row['title']
    if row['year'] != 0 and not pd.isna(row['year']):
        return row['year']
    y = fetch_tmdb_year(title)
    if not y:
        y = fetch_anilist_year(title)
    return y or 0


print("📥 Loading dataset...")
df = pd.read_csv(INPUT_PATH)
print(f"➡️ Loaded {len(df)} entries")

# Only process missing years
df['year'].fillna(0, inplace=True)
mask_missing = (df['year'] == 0)
missing_df = df[mask_missing]
print(f"🕵️ {len(missing_df)} entries missing year info...")

start = time.time()
updated = 0

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(fetch_year, row): idx for idx, row in missing_df.iterrows()}
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        idx = futures[future]
        try:
            year = future.result()
            if year and year != 0:
                df.at[idx, 'year'] = int(year)
                updated += 1
        except Exception:
            continue

        if i % 200 == 0:
            print(f"{i}/{len(missing_df)} processed, {updated} new years filled...")
            df.to_csv(OUTPUT_PATH, index=False)

df.to_csv(OUTPUT_PATH, index=False)
print(f"🎯 Done! Added {updated} new years. Final dataset saved → {OUTPUT_PATH}")
