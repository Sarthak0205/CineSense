# evaluate_recommender.py
"""
Evaluation Script for HybridRecommender
---------------------------------------
- Checks dataset, embeddings, and clustering alignment
- Reports cosine similarity statistics
- Runs semantic sanity checks on key queries
"""

import numpy as np
import pandas as pd
from hybrid_recommender import HybridRecommender
from sklearn.metrics.pairwise import cosine_similarity

def inspect_embeddings(hr):
    print("\n🔍 Embedding Inspection")
    print("----------------------------------------------------")
    embs = hr.embeddings
    print(f"Shape: {embs.shape}")
    norms = np.linalg.norm(embs, axis=1)
    print(f"Norms: mean={norms.mean():.4f}, min={norms.min():.4f}, max={norms.max():.4f}")
    print(f"Any NaNs? {np.isnan(embs).any()}")

    # Cosine similarity diagnostics
    sample_idx = np.random.choice(len(embs), 5, replace=False)
    sim_matrix = cosine_similarity(embs[sample_idx])
    print("\nSample cosine similarity matrix:")
    print(np.round(sim_matrix, 3))

def inspect_clusters(hr):
    print("\n📊 Cluster Inspection")
    print("----------------------------------------------------")
    if "cluster" not in hr.data.columns:
        print("⚠️ No cluster column found.")
        return
    counts = hr.data["cluster"].value_counts().sort_index()
    print(f"Number of clusters: {len(counts)}")
    print("Top 5 cluster sizes:")
    print(counts.head())

def test_queries(hr):
    print("\n🎬 Recommender Sanity Test")
    print("----------------------------------------------------")
    test_titles = [
        "Inception", "The Dark Knight", "La La Land", "Parasite",
        "Loki", "Attack on Titan", "Death Note"
    ]
    for t in test_titles:
        print(f"\n🎯 Query: {t}")
        try:
            df = hr.recommend(t, top_n=5, verbose=False)
            if df.empty:
                print("   ⚠️ No results.")
                continue
            for _, row in df.iterrows():
                print(f"   → {row['title']} ({row['genre']} | {row['type']}, {int(row['year'])}) 🔹 cosine={row['cosine_score']:.3f} | final={row['overall_score']:.3f}")
        except Exception as e:
            print(f"   ❌ Error for '{t}': {e}")

def main():
    print("🧠 Loading Hybrid Recommender...")
    hr = HybridRecommender()
    inspect_embeddings(hr)
    inspect_clusters(hr)
    test_queries(hr)

if __name__ == "__main__":
    main()
