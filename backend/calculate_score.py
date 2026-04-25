# =========================================================
# 📊 CineSense Performance Comparison
# TF-IDF + Cosine  vs  Sentence-BERT + Cosine
# =========================================================

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error,
    precision_score, recall_score, f1_score
)
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

# =========================================================
# 1️⃣ Load Dataset and Embeddings
# =========================================================
data = pd.read_csv("data/final_dataset_clustered.csv")
print("✅ Columns in dataset:", data.columns.tolist())

# Fix column naming based on your dataset
required_cols = {
    "title": "title",
    "genre": "genres",
    "overview": "overview",
    "cluster": "cluster_id"
}

# Ensure all required columns exist safely
for key, col in required_cols.items():
    if col not in data.columns:
        data[col] = ''
    else:
        data[col] = data[col].fillna('')

# Combine text columns for TF-IDF
data['combined_text'] = (
    data['title'] + ' ' +
    data['genres'] + ' ' +
    data['overview']
)

# Load precomputed BERT embeddings
bert_embeddings = np.load("models/embeddings.npy")

# Align embeddings length with dataset
if len(bert_embeddings) != len(data):
    print(f"⚠️ Mismatch detected: {len(bert_embeddings)} embeddings vs {len(data)} dataset rows.")
    min_len = min(len(bert_embeddings), len(data))
    print(f"🔧 Truncating both to {min_len} entries for alignment.")
    bert_embeddings = bert_embeddings[:min_len]
    data = data.iloc[:min_len].reset_index(drop=True)

# =========================================================
# 2️⃣ Compute Similarities
# =========================================================
# TF-IDF Embeddings
tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
tfidf_matrix = tfidf.fit_transform(data['combined_text'])

tfidf_sim = cosine_similarity(tfidf_matrix)
bert_sim = cosine_similarity(bert_embeddings)

# Normalize similarities (0–1 range)
scaler = MinMaxScaler()
tfidf_sim = scaler.fit_transform(tfidf_sim)
bert_sim = scaler.fit_transform(bert_sim)

# =========================================================
# 3️⃣ Generate Ground Truth (same cluster = relevant)
# =========================================================
labels = LabelEncoder().fit_transform(data['cluster_id'].astype(str))

# Build ground truth binary similarity matrix (1 if same cluster)
n = len(labels)
ground_truth = np.zeros((n, n))
for i in range(n):
    ground_truth[i] = (labels == labels[i]).astype(int)

# =========================================================
# 4️⃣ Flatten matrices for metric computation
# =========================================================
mask = np.triu(np.ones_like(ground_truth, dtype=bool), k=1)
y_true = ground_truth[mask]
y_pred_tfidf = tfidf_sim[mask]
y_pred_bert = bert_sim[mask]

# Adaptive threshold (top 10% most similar pairs considered relevant)
tfidf_threshold = np.percentile(y_pred_tfidf, 90)
bert_threshold = np.percentile(y_pred_bert, 90)

y_pred_tfidf_bin = (y_pred_tfidf >= tfidf_threshold).astype(int)
y_pred_bert_bin = (y_pred_bert >= bert_threshold).astype(int)

# =========================================================
# 5️⃣ Evaluation Metrics
# =========================================================
metrics = {
    "RMSE": [
        np.sqrt(mean_squared_error(y_true, y_pred_tfidf)),
        np.sqrt(mean_squared_error(y_true, y_pred_bert))
    ],
    "MAE": [
        mean_absolute_error(y_true, y_pred_tfidf),
        mean_absolute_error(y_true, y_pred_bert)
    ],
    "Precision": [
        precision_score(y_true, y_pred_tfidf_bin, zero_division=0),
        precision_score(y_true, y_pred_bert_bin, zero_division=0)
    ],
    "Recall": [
        recall_score(y_true, y_pred_tfidf_bin, zero_division=0),
        recall_score(y_true, y_pred_bert_bin, zero_division=0)
    ],
    "F1-Score": [
        f1_score(y_true, y_pred_tfidf_bin, zero_division=0),
        f1_score(y_true, y_pred_bert_bin, zero_division=0)
    ]
}

results_df = pd.DataFrame(metrics, index=["TF-IDF + Cosine", "BERT + Cosine"])

# =========================================================
# 6️⃣ Display Results
# =========================================================
print("\n📈 Model Performance Comparison:\n")
print(results_df.round(3))

# Optional: Save to CSV for visualization
results_df.to_csv("data/model_comparison_results.csv", index=True)
print("\n💾 Results saved to data/model_comparison_results.csv")
