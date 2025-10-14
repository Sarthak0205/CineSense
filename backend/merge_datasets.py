import pandas as pd
import numpy as np
import re

# ───────────────────────────────
# 🔹 Utility: clean text safely
# ───────────────────────────────
def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)
    return text

def normalize_type(t):
    if not isinstance(t, str):
        return "unknown"
    t = t.lower().strip()
    mapping = {
        "movie": "movie",
        "movies": "movie",
        "film": "movie",
        "tv show": "series",
        "series": "series",
        "tv series": "series",
        "show": "series",
        "anime": "anime",
        "animes": "anime",
        "cartoon": "anime"
    }
    return mapping.get(t, "unknown")

# ───────────────────────────────
# 📥 Load datasets
# ───────────────────────────────
unified = pd.read_csv("data/unified_content_cleaned.csv")
dataset = pd.read_csv("data/dataset.csv")

# Ensure consistent columns
unified.columns = unified.columns.str.lower().str.strip()
dataset.columns = dataset.columns.str.lower().str.strip()

# ───────────────────────────────
# 🧩 Normalize common columns
# ───────────────────────────────
# For unified
if "overview" in unified.columns:
    unified.rename(columns={"overview": "description"}, inplace=True)
if "vote_average" in unified.columns:
    unified.rename(columns={"vote_average": "rating"}, inplace=True)

# For dataset
if "overview" in dataset.columns:
    dataset.rename(columns={"overview": "description"}, inplace=True)
if "vote_average" in dataset.columns:
    dataset.rename(columns={"vote_average": "rating"}, inplace=True)

# ───────────────────────────────
# 🔧 Minimal column set alignment
# ───────────────────────────────
base_columns = ["title", "type", "genre", "description", "rating", "release_date"]

for df in [unified, dataset]:
    for col in base_columns:
        if col not in df.columns:
            df[col] = np.nan
    df = df[base_columns]

# ───────────────────────────────
# ✨ Clean and Normalize
# ───────────────────────────────
for df in [unified, dataset]:
    df["title"] = df["title"].apply(clean_text).str.lower()
    df["genre"] = df["genre"].apply(clean_text)
    df["description"] = df["description"].apply(clean_text)
    df["type"] = df["type"].apply(normalize_type)

# Remove empty titles
unified = unified[unified["title"].notna() & (unified["title"].str.strip() != "")]
dataset = dataset[dataset["title"].notna() & (dataset["title"].str.strip() != "")]

# ───────────────────────────────
# 🔁 Merge + Deduplicate
# ───────────────────────────────
merged = pd.concat([unified, dataset], ignore_index=True)
merged.drop_duplicates(subset=["title", "type"], keep="first", inplace=True)

# Handle missing ratings
merged["rating"] = pd.to_numeric(merged["rating"], errors="coerce").fillna(0)

# Ensure type consistency
merged["type"] = merged["type"].apply(normalize_type)

# ───────────────────────────────
# 📅 Extract Year
# ───────────────────────────────
if "release_date" in merged.columns:
    merged["year"] = pd.to_datetime(merged["release_date"], errors="coerce").dt.year.fillna(0).astype(int)
else:
    merged["year"] = 0

# ───────────────────────────────
# ✅ Final Cleaned Dataset
# ───────────────────────────────
merged.reset_index(drop=True, inplace=True)
print(f"✅ Merged dataset created with {len(merged)} unique titles")
print("📊 Type distribution:")
print(merged["type"].value_counts())

# ───────────────────────────────
# 💾 Save merged dataset
# ───────────────────────────────
merged.to_csv("merged_unified_dataset.csv", index=False)
print("\n💾 Saved as 'merged_unified_dataset.csv'")
