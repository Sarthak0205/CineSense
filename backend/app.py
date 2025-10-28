import os
import json
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from bson import ObjectId
from fuzzywuzzy import process  # ✅ Fuzzy matching

from hybrid_recommender import recommend, get_all_titles  # ✅ We'll use this to fetch dataset titles
from db import init_db, mongo
from utils.helpers import get_poster_url

# ======================================
# Flask App Setup
# ======================================
app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Flask Configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/cineSenseDB")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "supersecretkey123")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))

init_db(app)
jwt = JWTManager(app)

# ======================================
# Register Blueprints
# ======================================
from routes.auth_routes import auth_bp
from routes.favorites_routes import favorites_bp
from routes.personalized_routes import personal_bp

app.register_blueprint(auth_bp)
app.register_blueprint(favorites_bp)
app.register_blueprint(personal_bp)

# ======================================
# Routes
# ======================================
@app.route("/api", methods=["GET"])
def home():
    return jsonify({"message": "🎬 CineSense API running!"})


# ───────────────────────────────
# 🔹 Hybrid Recommendation API
# ───────────────────────────────
@app.route("/api/recommend", methods=["POST"])
def get_recommendations():
    """Return hybrid recommendations for a given title (with fuzzy matching fallback)."""
    try:
        data = request.get_json()
        title = data.get("title", "").strip()
        top_k = int(data.get("top_k", 10))
        type_ = data.get("type", "movie").lower()

        if not title:
            return jsonify({"success": False, "message": "❌ No title provided"}), 400

        # Normalize type for consistency
        type_map = {
            "tv": "series",
            "show": "series",
            "series": "series",
            "film": "movie",
            "movie": "movie",
            "movies": "movie",
            "anime": "anime",
            "animes": "anime",
        }
        type_ = type_map.get(type_, "movie")

        # Try to get recommendations directly
        result = recommend(title, top_k=top_k)

        # If not found, use fuzzy matching
        if not result.get("success"):
            all_titles = get_all_titles()  # Get all titles from your dataset
            match, score = process.extractOne(title, all_titles)
            if score >= 75:
                print(f"🔍 Using fuzzy match: '{title}' → '{match}' (score: {score})")
                result = recommend(match, top_k=top_k)
            else:
                return jsonify({
                    "success": False,
                    "message": f"'{title}' not found in dataset (no close match)."
                }), 404

        recs = result.get("results", [])
        if recs:
            max_sim = max(r.get("similarity", 0) for r in recs) or 1
            for r in recs:
                r["match_percent"] = round((r.get("similarity", 0) / max_sim) * 100, 1)
                r["poster_url"] = get_poster_url(r["title"], r.get("type", type_))

        return jsonify({"success": True, "results": recs}), 200

    except Exception as e:
        print("❌ Error in /api/recommend:", e)
        return jsonify({"success": False, "message": str(e)}), 500


# ───────────────────────────────
# 🔹 Poster Fetch API
# ───────────────────────────────
@app.route("/api/poster/<string:title>", methods=["GET"])
def get_poster(title):
    """Return a poster URL for a given title with type-based fallback."""
    try:
        title = title.replace("%20", " ").strip()
        content_type = request.args.get("type", "movie").lower()

        type_map = {
            "tv": "series",
            "show": "series",
            "series": "series",
            "film": "movie",
            "movie": "movie",
            "movies": "movie",
            "anime": "anime",
            "animes": "anime",
        }
        content_type = type_map.get(content_type, "movie")

        poster_url = get_poster_url(title, content_type)
        return jsonify({"title": title, "type": content_type, "poster": poster_url}), 200

    except Exception as e:
        print(f"❌ Poster fetch error for {title}: {e}")
        return jsonify({
            "title": title,
            "poster": "https://via.placeholder.com/500x750?text=Poster+Unavailable",
            "error": str(e)
        }), 500


# ───────────────────────────────
# 🔹 MongoDB Connection Test
# ───────────────────────────────
@app.route("/test_db", methods=["GET"])
def test_db():
    """Quick sanity test for MongoDB connection."""
    try:
        mongo.db.users.insert_one({"test": "ok"})
        count = mongo.db.users.count_documents({})
        return jsonify({"success": True, "count": count}), 200
    except Exception as e:
        print("❌ DB connection error:", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ======================================
# Run Server
# ======================================
if __name__ == "__main__":
    print("✅ Flask backend running at http://127.0.0.1:5000/api")
    app.run(debug=True)
