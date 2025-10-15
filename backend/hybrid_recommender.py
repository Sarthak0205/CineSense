# hybrid_recommender.py

import os
import re
import pickle
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    HAS_S_BERT = True
except Exception:
    HAS_S_BERT = False


class HybridRecommender:
    def __init__(
        self,
        dataset_path="data/final_dataset.csv",
        embeddings_path="data/embeddings.npy",
        clusters_path="data/kmeans.pkl",
        n_clusters=20,
        sbert_model_name="all-MiniLM-L6-v2",
        recompute=False
    ):
        print("📥 Loading dataset...")
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")

        self.data = pd.read_csv(dataset_path)
        self.dataset_path = dataset_path
        self.embeddings_path = embeddings_path
        self.clusters_path = clusters_path
        self.n_clusters = n_clusters
        self.sbert_model_name = sbert_model_name

        # Basic cleanup
        for col in ["title", "genre", "description", "type", "rating", "year"]:
            if col not in self.data.columns:
                self.data[col] = "" if col in ["title", "genre", "description", "type"] else 0

        self.data["title"] = self.data["title"].astype(str).str.strip()
        self.data["type"] = self.data["type"].astype(str).str.lower().fillna("unknown")
        self.data["type"] = self.data["type"].replace({
            "movies": "movie", "films": "movie", "film": "movie",
            "tv": "series", "tv show": "series", "web series": "series",
            "animes": "anime"
        })

        # Detect anime more reliably
        def detect_anime(row):
            t = str(row.get("type", "")).lower()
            txt = f"{row.get('title','')} {row.get('genre','')} {row.get('description','')}".lower()
            if "anime" in t or "manga" in txt or "japan" in txt:
                return "anime"
            return t or "unknown"
        self.data["type"] = self.data.apply(detect_anime, axis=1)

        self._prepare_stats()

        # --- Load or compute embeddings ---
        if HAS_S_BERT:
            if not recompute and os.path.exists(embeddings_path):
                print("✅ Loading precomputed embeddings...")
                self.embeddings = np.load(embeddings_path)
            else:
                print("🔹 Computing embeddings...")
                self.sbert = SentenceTransformer(sbert_model_name)
                texts = (self.data["title"].fillna("") + " " +
                         self.data["genre"].fillna("") + " " +
                         self.data["description"].fillna("")).tolist()
                self.embeddings = self.sbert.encode(texts, show_progress_bar=True, convert_to_numpy=True)
                os.makedirs(os.path.dirname(embeddings_path) or ".", exist_ok=True)
                np.save(embeddings_path, self.embeddings)
                print(f"✅ Saved embeddings to {embeddings_path}")
        else:
            raise RuntimeError("SentenceTransformer not installed — please install 'sentence-transformers'.")

        # --- Load or compute clusters ---
        if not recompute and os.path.exists(clusters_path):
            print("✅ Loading precomputed clusters...")
            with open(clusters_path, "rb") as f:
                saved = pickle.load(f)
            self.kmeans = saved["kmeans"]
            self.data["cluster"] = saved["clusters"]
        else:
            print("🔹 Performing KMeans clustering...")
            km = KMeans(n_clusters=min(n_clusters, max(2, len(self.data)//20)), random_state=42, n_init=10)
            clusters = km.fit_predict(self.embeddings)
            self.kmeans = km
            self.data["cluster"] = clusters
            with open(clusters_path, "wb") as f:
                pickle.dump({"kmeans": self.kmeans, "clusters": clusters}, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"✅ Saved clusters to {clusters_path}")

        # Build quick lookup maps
        self.title_map = {t.lower(): i for i, t in enumerate(self.data["title"].astype(str))}
        self._compute_normalizers()
        print("✅ Model initialized and ready!")

    # ─────────────────────────────
    # Preprocessing helpers
    # ─────────────────────────────
    def _prepare_stats(self):
        if "rating" in self.data.columns:
            self.data["rating"] = pd.to_numeric(self.data["rating"], errors="coerce").fillna(0.0)
        else:
            self.data["rating"] = 0.0
        if "popularity" not in self.data.columns:
            if "members" in self.data.columns:
                self.data["popularity"] = pd.to_numeric(self.data["members"], errors="coerce").fillna(0)
            elif "score" in self.data.columns:
                self.data["popularity"] = pd.to_numeric(self.data["score"], errors="coerce").fillna(0)
            else:
                self.data["popularity"] = 0
        else:
            self.data["popularity"] = pd.to_numeric(self.data["popularity"], errors="coerce").fillna(0)
        if "year" not in self.data.columns:
            if "release_date" in self.data.columns:
                self.data["year"] = pd.to_datetime(self.data["release_date"], errors="coerce").dt.year.fillna(0).astype(int)
            else:
                self.data["year"] = 0
        else:
            self.data["year"] = pd.to_numeric(self.data["year"], errors="coerce").fillna(0).astype(int)

    def _compute_normalizers(self):
        self.rating_max = max(self.data["rating"].max(), 1)
        self.pop_max = max(self.data["popularity"].max(), 1)
        years = self.data["year"]
        self.year_max = years.max() if years.max() > 0 else 2025
        self.year_min = years[years > 0].min() if any(years > 0) else self.year_max

    # ─────────────────────────────
    # Utility and scoring
    # ─────────────────────────────
    def find_title_index(self, query_title):
        q = str(query_title).strip().lower()
        if q in self.title_map:
            return self.title_map[q]
        try:
            import difflib
            candidates = difflib.get_close_matches(q, list(self.title_map.keys()), n=1, cutoff=0.6)
            if candidates:
                return self.title_map[candidates[0]]
        except Exception:
            pass
        return None

    def _normalize_rating(self, r): return float(r) / self.rating_max
    def _normalize_pop(self, p): return float(p) / self.pop_max
    def _recency_score(self, y):
        try: y = int(y)
        except: return 0.0
        if y <= 0: return 0.0
        if self.year_max == self.year_min: return 0.5
        return (y - self.year_min) / (self.year_max - self.year_min)

    def _is_same_franchise(self, a, b):
        a_base = re.sub(r"[:\-–(].*", "", str(a).lower()).strip()
        b_base = re.sub(r"[:\-–(].*", "", str(b).lower()).strip()
        if not a_base or not b_base: return False
        if a_base in b_base or b_base in a_base: return True
        wa, wb = set(a_base.split()), set(b_base.split())
        return len(wa & wb) / max(1, len(wa | wb)) >= 0.6

    # ─────────────────────────────
    # Core recommendation logic
    # ─────────────────────────────
    def recommend(self, query_title, content_type=None, top_n=10, sort_mode=None, weights=None, verbose=False):
        """
        Returns same-type recommendations with flexible sorting:
        - content_type: 'anime' | 'movie' | 'series'
        - sort_mode: 'latest', 'oldest', 'popular', 'top_rated' (optional)
        """
        if weights is None:
            weights = {"sim": 0.5, "rating": 0.25, "pop": 0.15, "recency": 0.10}

        idx = self.find_title_index(query_title)
        if idx is None:
            if verbose: print(f"⚠️ '{query_title}' not found.")
            return None

        query_row = self.data.iloc[idx]
        query_type = str(query_row.get("type", "unknown"))
        desired_type = (content_type or query_type).lower().strip()

        # Strict same-type enforcement
        cluster_id = int(query_row["cluster"])
        cluster_peers = self.data[(self.data["cluster"] == cluster_id) & (self.data["type"] == desired_type)]

        if cluster_peers.empty:
            if verbose: print(f"⚠️ No {desired_type} peers in cluster {cluster_id}, using global pool.")
            cluster_peers = self.data[self.data["type"] == desired_type]

        if cluster_peers.empty:
            if verbose: print(f"⚠️ No '{desired_type}' items in dataset, fallback to all types.")
            cluster_peers = self.data.copy()

        # Compute cosine similarity
        q_vec = self.embeddings[idx].reshape(1, -1)
        sims = cosine_similarity(q_vec, self.embeddings[cluster_peers.index])[0]
        cluster_peers = cluster_peers.assign(similarity=sims)

        # Normalize features
        cluster_peers["rating_norm"] = cluster_peers["rating"].apply(self._normalize_rating)
        cluster_peers["pop_norm"] = cluster_peers["popularity"].apply(self._normalize_pop)
        cluster_peers["recency_norm"] = cluster_peers["year"].apply(self._recency_score)

        # Replace missing ratings
        zero_mask = cluster_peers["rating"] <= 0
        if zero_mask.any():
            mean_r = cluster_peers.loc[~zero_mask, "rating"].mean() or self.data["rating"].mean()
            cluster_peers.loc[zero_mask, "rating_norm"] = self._normalize_rating(mean_r)

        # Weighted score
        cluster_peers["final_score"] = (
            weights["sim"] * cluster_peers["similarity"] +
            weights["rating"] * cluster_peers["rating_norm"] +
            weights["pop"] * cluster_peers["pop_norm"] +
            weights["recency"] * cluster_peers["recency_norm"]
        )

        # Remove self
        cluster_peers = cluster_peers[cluster_peers["title"].str.lower() != query_row["title"].lower()]

        # Optional sort modes
        if sort_mode == "latest":
            cluster_peers = cluster_peers.sort_values("year", ascending=False)
        elif sort_mode == "oldest":
            cluster_peers = cluster_peers.sort_values("year", ascending=True)
        elif sort_mode == "popular":
            cluster_peers = cluster_peers.sort_values("popularity", ascending=False)
        elif sort_mode == "top_rated":
            cluster_peers = cluster_peers.sort_values("rating", ascending=False)
        else:
            cluster_peers = cluster_peers.sort_values("final_score", ascending=False)

        # Deduplicate franchises
        filtered, seen = [], []
        for _, r in cluster_peers.iterrows():
            base = re.sub(r"[:\-–(].*", "", str(r['title']).lower()).strip()
            if any(self._is_same_franchise(base, s) for s in seen):
                continue
            seen.append(base)
            filtered.append(r)
            if len(filtered) >= top_n * 3:
                break

        if not filtered:
            return cluster_peers.head(top_n)

        result = pd.DataFrame(filtered).head(top_n).reset_index(drop=True)
        return result[["title", "genre", "rating", "year", "similarity", "final_score", "type", "cluster"]]

    # ─────────────────────────────
    # For visualization
    # ─────────────────────────────
    def cluster_sample(self, cluster_id, n=10):
        return self.data[self.data["cluster"] == cluster_id].head(n)[["title", "type", "genre", "year"]]


if __name__ == "__main__":
    hr = HybridRecommender("data/final_dataset.csv", n_clusters=25)
    print(hr.recommend("inception", content_type="movie", top_n=10, verbose=True))
