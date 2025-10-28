import os
import torch
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.manifold import TSNE

# =====================================================
# 1️⃣ Load Dataset and Embeddings
# =====================================================
print("📥 Loading CineSense dataset and embeddings...")
DATA_PATH = "data/final_dataset_clustered.csv"
EMBED_CACHE = "data/embeddings_cache.pt"

df = pd.read_csv(DATA_PATH)
embeddings = torch.load(EMBED_CACHE)

# Normalize embedding format
if isinstance(embeddings, dict):
    embeddings = torch.stack(list(embeddings.values()))
elif isinstance(embeddings, list):
    embeddings = torch.stack(embeddings)

print(f"✅ Loaded {len(df)} entries and embeddings of shape {embeddings.shape}")

# =====================================================
# 2️⃣ Ensure Required Columns Exist
# =====================================================
required_cols = ["title", "cluster_id", "genres", "type", "rating"]
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"❌ Missing column '{col}' in dataset!")

# =====================================================
# 3️⃣ Cluster Label Mapping
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

df["cluster_name"] = df["cluster_id"].map(cluster_labels).fillna("Other / Miscellaneous")

# =====================================================
# 4️⃣ Dimensionality Reduction (t-SNE)
# =====================================================
print("🌀 Running t-SNE projection (this may take a minute)...")
tsne = TSNE(n_components=2, perplexity=30, learning_rate=200, random_state=42)
emb_2d = tsne.fit_transform(embeddings.detach().cpu().numpy())

df["x"] = emb_2d[:, 0]
df["y"] = emb_2d[:, 1]

# =====================================================
# 5️⃣ Visualization
# =====================================================
plt.figure(figsize=(12, 8))
sns.scatterplot(
    data=df,
    x="x",
    y="y",
    hue="cluster_name",
    style="type",
    palette="tab10",
    alpha=0.8,
    s=50,
)

plt.title("🎬 CineSense — Semantic Clusters in Recommender Embedding Space", fontsize=16, weight="bold")
plt.xlabel("t-SNE Dimension 1 (Semantic Axis 1)", fontsize=12)
plt.ylabel("t-SNE Dimension 2 (Semantic Axis 2)", fontsize=12)
plt.legend(title="Cluster / Genre Group", bbox_to_anchor=(1.05, 1), loc="upper left")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# =====================================================
# 6️⃣ Optional: Inspect Cluster Examples
# =====================================================
for cid, cname in cluster_labels.items():
    examples = df[df["cluster_id"] == cid]["title"].head(5).tolist()
    if examples:
        print(f"\n📦 {cid} — {cname}")
        for t in examples:
            print(f"   • {t}")
