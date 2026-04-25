import os
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer, util

# =====================================================
# 1️⃣ Load Dataset
# =====================================================
print("📥 Loading dataset...")
DATA_PATH = "data/final_dataset_v2.csv"
EMBED_CACHE = "data/embeddings_cache.pt"

df = pd.read_csv(DATA_PATH)

required_cols = ["title", "cluster_id", "genres", "type", "overview"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"❌ Missing columns: {missing}")

df.dropna(subset=["title", "overview"], inplace=True)
df.reset_index(drop=True, inplace=True)

# Normalize
df["genres"] = df["genres"].fillna("").str.lower()
df["type"] = df["type"].fillna("").str.lower()
df["format"] = df.get("format", "").fillna("").str.lower()

print(f"✅ Loaded {len(df)} titles")

# =====================================================
# 2️⃣ Build Semantic Text (NO TITLE)
# =====================================================
def build_semantic_text(row):
    return " ".join([
        str(row["overview"]),
        str(row["genres"]),
        str(row["type"]),
        str(row["format"])
    ])

df["semantic_text"] = df.apply(build_semantic_text, axis=1)

# =====================================================
# 3️⃣ Embeddings
# =====================================================
print("⚙️ Loading model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

if os.path.exists(EMBED_CACHE):
    print("📦 Loading cached embeddings...")
    embeddings = torch.load(EMBED_CACHE)
else:
    print("🧠 Generating embeddings...")
    embeddings = model.encode(
        df["semantic_text"].tolist(),
        show_progress_bar=True,
        convert_to_tensor=True
    )
    torch.save(embeddings, EMBED_CACHE)
    print("💾 Cached embeddings")

df["embedding_idx"] = range(len(df))

# =====================================================
# 4️⃣ Helpers (Multi-Signal)
# =====================================================
def genre_overlap(g1, g2):
    if not g1 or not g2:
        return 0
    s1 = set(g.strip() for g in g1.split(","))
    s2 = set(g.strip() for g in g2.split(","))
    return len(s1 & s2) / max(len(s1), 1)

def format_score(f1, f2):
    return 1 if f1 and f1 == f2 else 0

def cluster_score(c1, c2):
    return 1 if c1 == c2 else 0

def title_penalty(q_title, c_title):
    q = set(q_title.lower().split())
    c = set(c_title.lower().split())
    return 1 if len(q & c) >= 1 else 0

# =====================================================
# 5️⃣ Recommendation Logic (MULTI-SIGNAL)
# =====================================================
def recommend(title, category=None, top_k=5):

    matches = df[df["title"].str.lower() == title.lower()]
    if matches.empty:
        return {"success": False, "message": f"'{title}' not found", "results": []}

    query = matches.iloc[0]
    query_emb = embeddings[query["embedding_idx"]]

    query_type = category.lower() if category else query["type"]
    query_format = str(query.get("format", "")).lower()
    query_cluster = query["cluster_id"]

    # Candidate pool (relaxed)
    candidates = df[
        (df["type"] == query_type) |
        (df["format"] == query_format)
    ]

    if candidates.empty:
        candidates = df

    cand_emb = embeddings[candidates["embedding_idx"].tolist()]
    cosine_scores = util.cos_sim(query_emb, cand_emb)[0]

    scored = []

    for i, (_, item) in enumerate(candidates.iterrows()):
        if item["title"].lower() == title.lower():
            continue

        semantic = float(cosine_scores[i])
        genre = genre_overlap(query["genres"], item["genres"])
        fmt = format_score(query_format, item["format"])
        cluster = cluster_score(query_cluster, item["cluster_id"])
        penalty = title_penalty(query["title"], item["title"])

        # 🔥 Multi-signal scoring
        final_score = (
            0.5 * semantic +
            0.2 * genre +
            0.2 * fmt +
            0.1 * cluster
            - 0.3 * penalty
        )

        scored.append((final_score, item))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, item in scored[:top_k]:
        results.append({
            "title": item["title"],
            "type": item["type"],
            "genres": item["genres"],
            "overview": item["overview"][:200] + "...",
            "format": item.get("format", ""),
            "cluster": item["cluster_id"],
            "score": round(score, 3)
        })

    return {
        "success": True,
        "message": "ok",
        "results": results
    }

# =====================================================
# 6️⃣ Helper
# =====================================================
def get_all_titles():
    return df["title"].dropna().tolist()

# =====================================================
# 7️⃣ Test
# =====================================================
if __name__ == "__main__":
    test_titles = [
        "friends",
        "the big bang theory",
        "spider-man",
        "the dark knight",
        "death note"
    ]

    for t in test_titles:
        print(f"\n🎬 Recommendations for: {t}")
        res = recommend(t, top_k=5)

        if not res["success"]:
            print(res["message"])
        else:
            for r in res["results"]:
                print(f"➡️ {r['title']} [{r['score']}] ({r['format']})")