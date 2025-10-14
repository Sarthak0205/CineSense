import os
import difflib
import re
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

class HybridRecommender:
    def __init__(self, dataset_path="data/final_dataset.csv", n_clusters=15):
        print("📥 Loading model and dataset...")
        self.dataset = pd.read_csv(dataset_path)
        self.dataset.dropna(subset=["title", "description"], inplace=True)
        self.dataset.reset_index(drop=True, inplace=True)

        # Normalize type field
        self.dataset["type"] = (
            self.dataset["type"]
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

        print("🔹 Loading SentenceTransformer model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        # Prepare combined textual features
        self.dataset["text"] = (
            self.dataset["title"].astype(str) + " " +
            self.dataset["genre"].astype(str) + " " +
            self.dataset["description"].astype(str)
        )

        print("🔹 Computing embeddings...")
        self.embeddings = self.model.encode(
            self.dataset["text"].tolist(),
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Cluster embeddings for DWM visualization
        print("🔹 Performing KMeans clustering...")
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.dataset["cluster"] = self.kmeans.fit_predict(self.embeddings)
        print("✅ Model initialized with clustering.")

    # ───────────────────────────────
    # 🔍 Title Matching
    # ───────────────────────────────
    def _find_closest_title(self, query_title):
        titles = self.dataset["title"].str.lower().tolist()
        query = query_title.lower().strip()
        matches = difflib.get_close_matches(query, titles, n=1, cutoff=0.6)
        if matches:
            matched_title = matches[0]
            print(f"🔎 Matched '{query_title}' → '{matched_title}'")
            return matched_title
        return None

    def _normalize_type(self, content_type):
        ct = content_type.lower()
        if "anime" in ct:
            return "anime"
        if any(x in ct for x in ["movie", "film"]):
            return "movie"
        if any(x in ct for x in ["series", "tv", "show", "drama"]):
            return "series"
        return "unknown"

    # ───────────────────────────────
    # 🎯 Recommendation Logic (Strict Type + Franchise Filtering)
    # ───────────────────────────────
    def recommend(self, title, content_type="movie", top_n=10):
        matched_title = self._find_closest_title(title)
        if not matched_title:
            print(f"⚠️ Title '{title}' not found in dataset.")
            return []

        query_type = self._normalize_type(content_type)

        idx = self.dataset[self.dataset["title"].str.lower() == matched_title].index
        if idx.empty:
            print(f"⚠️ Index not found for '{matched_title}'")
            return []
        idx = idx[0]

        query_vec = self.embeddings[idx]
        cluster_id = self.dataset.loc[idx, "cluster"]

        # Ensure the matched title belongs to same type
        actual_type = self.dataset.loc[idx, "type"]
        if actual_type != query_type:
            print(f"⚠️ '{matched_title}' type mismatch ({actual_type} vs {query_type}). Forcing type '{query_type}' recommendations only.")

        # ───────────────────────────────
        # 🧩 Step 1: Cluster and Type Filtering
        # ───────────────────────────────
        cluster_mask = self.dataset["cluster"] == cluster_id
        cluster_df = self.dataset.loc[cluster_mask].copy()
        same_type_cluster_df = cluster_df[cluster_df["type"] == query_type].copy()

        # ───────────────────────────────
        # 🔍 Step 2: Compute Similarity (Cluster Level)
        # ───────────────────────────────
        recs = pd.DataFrame(columns=["title", "genre", "rating", "description", "similarity"])
        if not same_type_cluster_df.empty:
            cluster_vectors = self.embeddings[same_type_cluster_df.index]
            sims = cosine_similarity(np.expand_dims(query_vec, axis=0), cluster_vectors)[0]
            same_type_cluster_df["similarity"] = sims
            recs = same_type_cluster_df[
                same_type_cluster_df["title"].str.lower() != matched_title
            ].sort_values(by="similarity", ascending=False)

        # ───────────────────────────────
        # 🔁 Step 3: Global Fallback (Same Type Only)
        # ───────────────────────────────
        if len(recs) < top_n:
            print("⚠️ Not enough same-type items in cluster, adding global fallback...")
            global_df = self.dataset[self.dataset["type"] == query_type]
            global_vectors = self.embeddings[global_df.index]
            sims = cosine_similarity(np.expand_dims(query_vec, axis=0), global_vectors)[0]
            global_df = global_df.copy()
            global_df["similarity"] = sims
            global_df = global_df[global_df["title"].str.lower() != matched_title]
            fallback_recs = global_df.sort_values(by="similarity", ascending=False).head(top_n * 2)
            recs = pd.concat([recs, fallback_recs]).drop_duplicates(subset=["title"]).head(top_n * 2)

        # ───────────────────────────────
        # 🚫 Step 4: Franchise Deduplication
        # ───────────────────────────────
        def same_franchise(t1, t2):
            t1_base = re.sub(r"[:\-–(].*", "", t1.lower()).strip()
            t2_base = re.sub(r"[:\-–(].*", "", t2.lower()).strip()
            words1 = set(t1_base.split())
            words2 = set(t2_base.split())
            return len(words1 & words2) >= min(2, len(words1))

        filtered = []
        seen_bases = set()
        for _, row in recs.iterrows():
            base_name = re.sub(r"[:\-–(].*", "", row['title'].lower()).strip()
            if any(same_franchise(base_name, b) for b in seen_bases):
                continue
            seen_bases.add(base_name)
            filtered.append(row)

        recs = pd.DataFrame(filtered).sort_values(by="similarity", ascending=False).head(top_n)

        # ───────────────────────────────
        # ✅ Return Clean Recommendations
        # ───────────────────────────────
        print(f"🎯 Found {len(recs)} unique {query_type} recommendations for '{matched_title}' (cluster {cluster_id})")
        return recs[["title", "genre", "rating", "description", "similarity"]]
