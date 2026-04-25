import pandas as pd

INPUT_PATH = "data/final_dataset_refined.csv"
OUTPUT_PATH = "data/final_dataset_v2.csv"

df = pd.read_csv(INPUT_PATH)

# -------------------------------------------------
# 1️⃣ Clean & normalize base columns
# -------------------------------------------------
df["overview"] = df["overview"].fillna("").astype(str)
df["genres"] = df["genres"].fillna("").astype(str).str.lower()
df["type"] = df["type"].fillna("").astype(str).str.lower()

# -------------------------------------------------
# 2️⃣ Infer FORMAT (global, rule-based)
# -------------------------------------------------
def infer_format(row):
    text = f"{row['overview']} {row['genres']}".lower()
    t = row["type"]

    # Anime
    if t == "anime" or "anime" in text:
        return "anime"

    # Sitcom / episodic comedy
    if (
        "sitcom" in text
        or "group of friends" in text
        or "roommates" in text
        or "workplace comedy" in text
        or ("comedy" in text and "series" in t)
    ):
        return "sitcom"

    # Superhero
    if any(k in text for k in ["superhero", "marvel", "dc comics"]):
        return "superhero"

    # Crime drama
    if any(k in text for k in ["crime", "drug", "gang", "cartel", "mafia"]):
        return "crime-drama"

    # Thriller / mystery
    if any(k in text for k in ["thriller", "mystery", "investigation"]):
        return "thriller"

    # Reality
    if any(k in text for k in ["reality", "competition", "talent show"]):
        return "reality"

    # Family / light
    if any(k in text for k in ["family", "kids", "children"]):
        return "family"

    return "general"

df["format"] = df.apply(infer_format, axis=1)

# -------------------------------------------------
# 3️⃣ Normalize GENRE TAGS (controlled vocabulary)
# -------------------------------------------------
GENRE_KEYWORDS = {
    "sitcom": ["sitcom"],
    "comedy": ["comedy", "humor"],
    "crime": ["crime", "gang", "mafia"],
    "thriller": ["thriller", "suspense"],
    "psychological": ["psychological", "mind", "mental"],
    "action": ["action", "fight", "battle"],
    "adventure": ["adventure", "journey"],
    "romance": ["romance", "love"],
    "drama": ["drama"],
    "superhero": ["superhero"],
    "anime": ["anime"],
    "sci-fi": ["sci-fi", "science fiction"],
    "fantasy": ["fantasy", "magic"],
}

def build_genre_tags(text):
    tags = set()
    text = text.lower()
    for tag, keys in GENRE_KEYWORDS.items():
        if any(k in text for k in keys):
            tags.add(tag)
    return ", ".join(sorted(tags))

df["genre_tags"] = df.apply(
    lambda r: build_genre_tags(f"{r['genres']} {r['overview']} {r['format']}"),
    axis=1
)

# -------------------------------------------------
# 4️⃣ Final sanity checks
# -------------------------------------------------
# Ensure no empty formats
df["format"] = df["format"].replace("", "general")

# Ensure genre_tags is never empty
df["genre_tags"] = df["genre_tags"].replace("", "general")

# -------------------------------------------------
# 5️⃣ Save refined dataset
# -------------------------------------------------
df.to_csv(OUTPUT_PATH, index=False)
print(f"✅ Dataset refined and saved as: {OUTPUT_PATH}")

# Optional: quick stats
print("\n📊 Format distribution:")
print(df["format"].value_counts().head(10))

print("\n📊 Genre tag samples:")
print(df["genre_tags"].value_counts().head(10))
