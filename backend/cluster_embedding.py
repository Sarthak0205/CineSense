import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import joblib

# Load dataset
df = pd.read_csv("data/final_dataset.csv")

# Generate embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")
texts = (df["title"] + " " + df["genre"].fillna("") + " " + df["description"].fillna("")).tolist()
embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

# Cluster (you can tune n_clusters)
n_clusters = 20
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
labels = kmeans.fit_predict(embeddings)
df["cluster"] = labels

# Save
df.to_csv("data/final_dataset_clustered.csv", index=False)
joblib.dump(kmeans, "models/kmeans_model.pkl")
np.save("models/embeddings.npy", embeddings)
print(f"✅ Clustering complete — {n_clusters} clusters assigned.")
