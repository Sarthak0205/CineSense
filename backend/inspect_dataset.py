import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns

# === Step 1: Load dataset ===
print("📥 Loading clustered dataset...")
df = pd.read_csv("data/final_dataset_clustered.csv")

print(f"✅ Loaded {len(df)} entries across {df['cluster_id'].nunique()} clusters.")
print(f"🧩 Columns: {list(df.columns)}\n")

# === Step 2: Genre analysis per cluster ===
cluster_summary = []

for cluster_id, group in df.groupby("cluster_id"):
    genres = (
        group["genres"]
        .dropna()
        .astype(str)
        .str.lower()
        .str.replace(" ", "")
        .str.split(",")
    )
    flat_genres = [g for sublist in genres for g in sublist if g]
    common_genres = Counter(flat_genres).most_common(6)
    cluster_summary.append({
        "cluster_id": cluster_id,
        "num_titles": len(group),
        "top_genres": ", ".join([f"{g} ({c})" for g, c in common_genres])
    })

cluster_df = pd.DataFrame(cluster_summary).sort_values("num_titles", ascending=False)
print("📊 Cluster Genre Summary:")
print(cluster_df.head(10))
print("\n")

# === Step 3: Representative samples ===
print("🎬 Representative Titles per Cluster:\n")

for cluster_id in cluster_df["cluster_id"].head(5):
    subset = df[df["cluster_id"] == cluster_id]
    print(f"\n🎯 Cluster {cluster_id} — {len(subset)} titles")
    print("Top genres:", cluster_df.loc[cluster_df['cluster_id'] == cluster_id, 'top_genres'].values[0])
    print(subset.sample(min(3, len(subset)), random_state=42)[["title", "genres", "overview"]])
    print("-" * 80)

# === Step 4: Optional — Genre frequency heatmap ===
print("\n📈 Generating genre-cluster heatmap...")

# Create a matrix of cluster vs genre counts
all_genres = set(
    g.strip().lower()
    for row in df["genres"].dropna()
    for g in row.split(",")
)

genre_list = sorted(all_genres)
heatmap_data = pd.DataFrame(0, index=sorted(df["cluster_id"].unique()), columns=genre_list)

for _, row in df.iterrows():
    if pd.isna(row["genres"]):
        continue
    genres = [g.strip().lower() for g in row["genres"].split(",")]
    for g in genres:
        heatmap_data.at[row["cluster_id"], g] += 1

# Plot top 10 genres by overall frequency
top_genres = heatmap_data.sum().sort_values(ascending=False).head(10).index
plt.figure(figsize=(10, 6))
sns.heatmap(heatmap_data[top_genres], cmap="YlGnBu", linewidths=0.5)
plt.title("🔥 Top Genre Distribution Across Clusters")
plt.xlabel("Genre")
plt.ylabel("Cluster ID")
plt.tight_layout()
plt.show()

print("✅ Analysis complete.")
