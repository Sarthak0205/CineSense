import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from tqdm import tqdm
import os

# ========= CONFIG =========
DATA_PATH = "data/final_dataset_polished.csv"   # or your latest dataset
OUTPUT_PATH = "data/final_dataset_clustered.csv"
MODEL_NAME = "all-MiniLM-L6-v2"  # balanced performance/speed
N_CLUSTERS = 15  # tune this number (10–20 usually good)
# ==========================

print("📥 Loading dataset...")
df = pd.read_csv(DATA_PATH)
print(f"✅ Loaded {len(df)} entries")

# Verify combined_text exists
if "combined_text" not in df.columns:
    df["combined_text"] = (
        df["title"].fillna('') + " | " +
        df["genres"].fillna('') + " | " +
        df["overview"].fillna('')
    )

# ========== EMBEDDINGS ==========
print(f"🧠 Loading Sentence Transformer model: {MODEL_NAME} ...")
model = SentenceTransformer(MODEL_NAME)

# Generate sentence embeddings
texts = df["combined_text"].astype(str).tolist()

print("⚙️ Generating embeddings (this may take a few minutes)...")
embeddings = model.encode(texts, batch_size=64, show_progress_bar=True, convert_to_numpy=True)

print("✅ Embeddings generated:", embeddings.shape)

# Optional: Normalize for better clustering performance
embeddings = normalize(embeddings)

# ========== CLUSTERING ==========
print(f"📊 Running K-Means clustering with {N_CLUSTERS} clusters...")
kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
df["cluster_id"] = kmeans.fit_predict(embeddings)

# Compute cluster centroids (optional, useful for visualization or summary)
cluster_sizes = pd.Series(df["cluster_id"]).value_counts().sort_index()
print("\n📈 Cluster size distribution:")
print(cluster_sizes)

# ========== SAVE ==========
os.makedirs("data", exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False)
print(f"\n💾 Saved enriched dataset with clusters → {OUTPUT_PATH}")

print("\n🎯 DONE!")
print("Columns now include: title, genres, overview, combined_text, cluster_id")
