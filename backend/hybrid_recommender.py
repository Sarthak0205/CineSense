import os
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer, util

# =====================================================
# 1️⃣ Load Dataset
# =====================================================
print("📥 Loading clustered dataset...")
DATA_PATH = "data/final_dataset_clustered.csv"
EMBED_CACHE = "data/embeddings_cache.pt"

df = pd.read_csv(DATA_PATH)

required_cols = ["title", "combined_text", "cluster_id", "genres", "type", "overview", "rating"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"❌ Missing columns: {missing}")

df.dropna(subset=["title", "combined_text"], inplace=True)
df.reset_index(drop=True, inplace=True)

print(f"✅ Loaded {len(df)} titles across {df['cluster_id'].nunique()} clusters.")

# =====================================================
# 2️⃣ Load or Generate Embeddings (Cached)
# =====================================================
print("⚙️ Loading SentenceTransformer model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

if os.path.exists(EMBED_CACHE):
    print("📦 Loading cached embeddings...")
    embeddings = torch.load(EMBED_CACHE)
else:
    print("🧠 Generating fresh embeddings (this may take several minutes)...")
    embeddings = model.encode(df["combined_text"].tolist(), show_progress_bar=True, convert_to_tensor=True)
    torch.save(embeddings, EMBED_CACHE)
    print(f"💾 Embeddings cached → {EMBED_CACHE}")

df["embedding_idx"] = range(len(df))

# =====================================================
# 3️⃣ Cluster Name Mapping (Optional)
# =====================================================
cluster_labels = {
    0: "Animated & Family",
    1: "Crime & Action Thrillers",
    2: "Emotional Drama / Slice of Life",
    3: "Psychological Horror",
    6: "Workplace & Situational Comedy",
    9: "Reality / Music / Performance",
    10: "Sci-Fi & Adventure",
    11: "Mystery / Investigative Thrillers",
    13: "Romantic / Relationship Stories",
    14: "Family Dramas & Lighthearted Shows",
}

# =====================================================
# 4️⃣ Hybrid Recommendation Logic with type restriction and duplicate filtering
# =====================================================
def recommend(title, category=None, top_k=5, expand_clusters=True):
    """
    Return top_k recommendations based on semantic + cluster similarity.
    Enforces type restriction:
     - If `category` is provided → force recommend only same category
     - Else → use dataset type of the input title
    """
    matches = df[df["title"].str.lower() == title.lower()]
    if matches.empty:
        return {"success": False, "message": f"'{title}' not found in dataset.", "results": []}

    idx = matches.index[0]
    query = df.loc[idx]
    query_emb = embeddings[query["embedding_idx"]]
    query_cluster = query["cluster_id"]

    # ✅ Normalize dataset type column
    df["type"] = df["type"].astype(str).str.strip().str.lower()

    # ✅ Determine the target type
    query_type = (
        category.lower()
        if category else (
            str(query["type"]).lower().strip() if isinstance(query["type"], str) else "movie"
        )
    )
    valid_types = ["movie", "series", "anime"]
    if query_type not in valid_types:
        query_type = "movie"

    print(f"🔍 Input: {title} | Category: {query_type}")

    # ✅ Filter candidates from same cluster + same category/type
    candidates = df[(df["cluster_id"] == query_cluster) & (df["type"] == query_type)]

    # Fallback if cluster too small
    if len(candidates) < 2:
        candidates = df[df["type"] == query_type]

    cand_emb = embeddings[candidates["embedding_idx"].tolist()]

    # Compute cosine similarities
    scores = util.cos_sim(query_emb, cand_emb)[0]
    top_indices = torch.topk(scores, k=min(len(candidates), top_k + 1))

    recs = []
    seen_titles = set()

    for score, local_idx in zip(top_indices[0], top_indices[1]):
        item = candidates.iloc[local_idx.item()]
        low_title = item["title"].lower()
        if low_title != title.lower() and low_title not in seen_titles:
            recs.append({
                "title": item["title"],
                "type": item["type"],
                "genres": item.get("genres", ""),
                "rating": item.get("rating", "N/A"),
                "overview": (item["overview"][:200] + "...") if isinstance(item["overview"], str) else "",
                "cluster": cluster_labels.get(item["cluster_id"], "Unknown"),
                "similarity": round(float(score), 3)
            })
            seen_titles.add(low_title)

    # Fallback global search (same type)
    if len(recs) < top_k and expand_clusters:
        needed = top_k - len(recs)
        global_scores = util.cos_sim(query_emb, embeddings)[0]

        type_mask = df["type"] == query_type
        candidate_indices = df[type_mask].index.tolist()

        filtered_scores = [(i, global_scores[i].item()) for i in candidate_indices]
        filtered_scores.sort(key=lambda x: x[1], reverse=True)

        for global_idx, score in filtered_scores:
            item = df.iloc[global_idx]
            low_title = item["title"].lower()
            if low_title != title.lower() and low_title not in seen_titles:
                recs.append({
                    "title": item["title"],
                    "type": item["type"],
                    "genres": item.get("genres", ""),
                    "rating": item.get("rating", "N/A"),
                    "overview": (item["overview"][:200] + "...") if isinstance(item["overview"], str) else "",
                    "cluster": cluster_labels.get(item["cluster_id"], "Unknown"),
                    "similarity": round(float(score), 3)
                })
                seen_titles.add(low_title)
            if len(recs) >= top_k:
                break

    return {
        "success": bool(recs),
        "message": "ok" if recs else "no recommendations found",
        "results": sorted(recs, key=lambda x: x["similarity"], reverse=True)[:top_k]
    }

# =====================================================
# 4️⃣.5️⃣ Helper for Fuzzy Matching (for Flask API)
# =====================================================
def get_all_titles():
    """Return all titles in the dataset (used for fuzzy matching)."""
    return df["title"].dropna().tolist()

# =====================================================
# 5️⃣ Test Run (CLI)
# =====================================================
if __name__ == "__main__":
    test_title = "attack on titan"
    print(f"\n🎬 Recommendations for: {test_title}")
    result = recommend(test_title, top_k=10)

    if not result["success"]:
        print(result["message"])
    else:
        for r in result["results"]:
            print(f"➡️ {r['title']} ({r['cluster']}) [{r['similarity']}] - {r['genres']}")
