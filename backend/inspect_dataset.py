import pandas as pd
import re

# 🔹 Path to your dataset
DATA_PATH = "data/final_dataset.csv"
OUTPUT_PATH = "data/cleaned_final_dataset.csv"

print("📥 Loading dataset...")
df = pd.read_csv(DATA_PATH)

# 🔹 Normalize columns
df.columns = [c.lower().strip() for c in df.columns]

# Drop incomplete or empty titles/descriptions
df.dropna(subset=["title", "description"], inplace=True)
df = df[df["title"].str.strip() != ""]

# 🔹 Normalize the 'type' column
df["type"] = (
    df["type"]
    .astype(str)
    .str.lower()
    .replace({
        "tv": "series",
        "web series": "series",
        "show": "series",
        "film": "movie",
        "movies": "movie",
    })
    .fillna("unknown")
)

# 🔹 Fix anime detection by checking keywords
def fix_type(row):
    text = f"{row['title']} {row['genre']} {row['description']}".lower()
    if any(k in text for k in ["anime", "manga", "japanese animation"]):
        return "anime"
    if any(k in text for k in ["series", "tv", "show", "drama", "episodes"]):
        return "series"
    if any(k in text for k in ["movie", "film", "cinema", "sci-fi", "thriller", "comedy", "action"]):
        return "movie"
    return row["type"]

df["type"] = df.apply(fix_type, axis=1)

# 🔹 Remove wrong-type noise (anime labeled as movie, etc.)
def remove_wrong_types(row):
    text = f"{row['title']} {row['genre']}".lower()
    if row["type"] == "anime" and not any(k in text for k in ["anime", "manga", "japanese animation"]):
        return None
    if row["type"] != "anime" and any(k in text for k in ["anime", "manga"]):
        return None
    return row["type"]

df["type"] = df.apply(remove_wrong_types, axis=1, result_type=None)
df.dropna(subset=["type"], inplace=True)

# 🔹 Deduplicate by title
df = df.drop_duplicates(subset=["title"], keep="first")

# 🔹 Clean text fields
def clean_text(t):
    return re.sub(r"\s+", " ", str(t)).strip()

for col in ["title", "genre", "description"]:
    df[col] = df[col].apply(clean_text)

# 🔹 Remove entries with extremely short descriptions
df = df[df["description"].str.len() > 25]

# 🔹 Reset index
df.reset_index(drop=True, inplace=True)

print(f"✅ Cleaned dataset: {len(df)} entries remaining")
print(df["type"].value_counts())

# 🔹 Save cleaned version
df.to_csv(OUTPUT_PATH, index=False)
print(f"💾 Cleaned dataset saved → {OUTPUT_PATH}")
