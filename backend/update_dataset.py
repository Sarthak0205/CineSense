import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# ───────────────────────────────
# 🔹 Setup
# ───────────────────────────────
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

INPUT_FILE = "data/final_dataset_final.csv"
OUTPUT_FILE = "data/final_dataset_polished.csv"

# ───────────────────────────────
# 🔹 Helper Function: Fetch Year from TMDB
# ───────────────────────────────
def fetch_year(title):
    """Fetch release year from TMDB based on title."""
    try:
        url = f"https://api.themoviedb.org/3/search/multi"
        params = {"api_key": TMDB_API_KEY, "query": title}
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        if data["results"]:
            item = data["results"][0]
            date = item.get("release_date") or item.get("first_air_date")
            if date and len(date) >= 4:
                return int(date[:4])
    except Exception:
        pass
    return 0  # return 0 if not found

# ───────────────────────────────
# 🔹 Main Logic
# ───────────────────────────────
def fill_missing_years(limit=300):
    print("📥 Loading dataset...")
    df = pd.read_csv(INPUT_FILE)
    print(f"✅ Loaded {len(df)} entries")

    missing_mask = (df["year"] == 0)
    missing_count = missing_mask.sum()
    print(f"🔍 Titles with missing year: {missing_count}")

    if missing_count == 0:
        print("✅ No missing years found.")
        return

    to_update = df[missing_mask].sample(min(limit, missing_count), random_state=42)
    print(f"⚙️ Fetching years for {len(to_update)} titles...")

    filled = 0
    start_time = time.time()

    for idx, row in to_update.iterrows():
        title = row["title"]
        year = fetch_year(title)
        if year:
            df.at[idx, "year"] = year
            filled += 1

        if filled % 20 == 0:
            print(f"🔸 {filled} years filled so far...")

        time.sleep(0.25)  # small delay to avoid rate limits

    duration = round(time.time() - start_time, 2)
    print(f"\n✅ Filled {filled} years in {duration}s")

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"💾 Saved polished dataset → {OUTPUT_FILE}")

# ───────────────────────────────
# 🔹 Run
# ───────────────────────────────
if __name__ == "__main__":
    fill_missing_years(limit=300)
