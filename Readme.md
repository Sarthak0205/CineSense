# 🎬 CineSense — Hybrid Recommender System

CineSense is an intelligent hybrid recommender system for Movies, Series, and Anime built using **Flask**, **Sentence Transformers**, and **KMeans Clustering**.  
It features a beautiful 3D visualization of clusters using **t-SNE** and **Plotly**.

---

## 🚀 Features

- 🧠 **Hybrid Recommendation**: Uses content embeddings + clustering
- 🎯 **Smart Filtering**: Detects same franchise & content type
- 🌌 **3D Cluster Visualization**: Interactive Plotly t-SNE map
- 🎞️ **Poster Fetching**: Uses TMDB + Jikan APIs
- ⚙️ **Fast Flask Backend** for API responses

---

## 🧩 Tech Stack

**Backend:** Python, Flask, Scikit-learn, Sentence Transformers  
**Frontend:** (React / HTML / JS — if applicable)  
**Visualization:** Plotly 3D Scatter  
**APIs:** TMDB, Jikan

---

## 🧰 Setup Instructions

1. Clone this repository:
   ```bash
   git clone https://github.com/<your-username>/CineSense.git
   cd CineSense/backend
   ```

Create a virtual environment:

python -m venv venv
source venv/bin/activate # (Mac/Linux)
venv\Scripts\activate # (Windows)

Install dependencies:

pip install -r requirements.txt

Add your TMDB API key in .env:

TMDB_API_KEY=your_api_key_here

Run the Flask server:

python app.py
