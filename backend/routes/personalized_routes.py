import numpy as np
from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from db import mongo
from hybrid_recommender import recommend
from utils.helpers import get_poster_url  # ✅ ensure this returns poster URLs

# 🔹 Blueprint
personal_bp = Blueprint("personalized", __name__, url_prefix="/api/personalized")


# ───────────────────────────────
# 🔸 Helper: Generate per-category personalized recs
# ───────────────────────────────
def generate_category_recommendations(uid, category):
    """
    Generate personalized recommendations for a user in a given category:
    'movies', 'series', or 'anime'.
    """
    user = mongo.db.users.find_one({"_id": ObjectId(uid)})
    if not user:
        return jsonify(success=False, message="User not found"), 404

    favorites = user.get("favorites", {})
    category_favs = []

    # Handle both new dict and old list formats
    if isinstance(favorites, list):
        category_favs = [f for f in favorites if f.get("type") == category]
    elif isinstance(favorites, dict):
        category_favs = favorites.get(category, [])

    if not category_favs:
        return jsonify(success=False, message=f"No {category} favorites yet"), 200

    combined = []
    for fav in category_favs:
        title = fav.get("title")
        if not title:
            continue
        try:
            res = recommend(title, category=category, top_k=10)
            if res.get("success"):
                combined.extend(res["results"])
        except Exception as e:
            current_app.logger.warning(f"Failed to recommend for {title}: {e}")

    if not combined:
        return jsonify(success=False, message="No recommendations found"), 404

    # Aggregate results, remove duplicates & already favorited
    fav_titles = {f.get("title") for f in category_favs if f.get("title")}
    seen = {}
    for rec in combined:
        title = rec["title"]
        sim = rec.get("similarity", 0)
        if title not in fav_titles:
            if title not in seen:
                seen[title] = {**rec, "type": category, "similarity": sim}
            else:
                seen[title]["similarity"] += sim

    recs = sorted(seen.values(), key=lambda x: x["similarity"], reverse=True)[:15]

    # ✅ Compute match_percent and poster fallback
    if recs:
        max_sim = max(r["similarity"] for r in recs) or 1
        for r in recs:
            r["match_percent"] = round((r["similarity"] / max_sim) * 100, 1)
            r["poster"] = get_poster_url(r["title"], category) or \
                "https://via.placeholder.com/500x750?text=Poster+Unavailable"

    return jsonify(success=True, results=recs), 200


# ───────────────────────────────
# 🔹 Category Endpoints
# ───────────────────────────────
@personal_bp.route("/movies", methods=["GET"])
@jwt_required()
def personalized_movies():
    """Personalized movie recommendations"""
    uid = get_jwt_identity()
    return generate_category_recommendations(uid, "movies")


@personal_bp.route("/series", methods=["GET"])
@jwt_required()
def personalized_series():
    """Personalized series recommendations"""
    uid = get_jwt_identity()
    return generate_category_recommendations(uid, "series")


@personal_bp.route("/anime", methods=["GET"])
@jwt_required()
def personalized_anime():
    """Personalized anime recommendations"""
    uid = get_jwt_identity()
    return generate_category_recommendations(uid, "anime")


# ───────────────────────────────
# 🔹 Global Personalized (mixed)
# ───────────────────────────────
@personal_bp.route("/", methods=["GET"])
@jwt_required()
def personalized_recommendations():
    """
    Personalized recommendations based on user's recent favorites.
    - Uses weighted scores (recent favorites get higher influence)
    - Returns match_percent & poster fallback
    """
    try:
        uid = get_jwt_identity()
        user = mongo.db.users.find_one({"_id": ObjectId(uid)}, {"favorites": 1})

        if not user:
            return jsonify(success=False, message="User not found"), 404

        favorites = user.get("favorites", {})
        titles = []

        # Handle both old list and new dict format
        if isinstance(favorites, list):
            titles = [f.get("title") for f in favorites if f.get("title")]
        elif isinstance(favorites, dict):
            for cat in ["movies", "series", "anime"]:
                titles.extend([f.get("title") for f in favorites.get(cat, []) if f.get("title")])

        if not titles:
            return jsonify(success=True, results=[], message="No favorites yet."), 200

        # Take last 5 favorites, weight recent ones more
        top_titles = titles[-5:]
        weights = np.linspace(1, 2, len(top_titles))  # more recent = heavier
        recommendations = []
        seen_titles = set(titles)

        for t, w in zip(top_titles, weights):
            try:
                res = recommend(t, top_k=10)
                if res.get("success"):
                    for r in res["results"]:
                        if r["title"] not in seen_titles:
                            sim = r.get("similarity", 0) * w
                            recommendations.append({
                                "title": r["title"],
                                "similarity": sim,
                                "type": r.get("type", "movies"),
                                "poster": get_poster_url(r["title"], r.get("type", "movies")),
                                "overview": r.get("overview", ""),
                            })
                            seen_titles.add(r["title"])
            except Exception as e:
                current_app.logger.warning(f"Recommendation failed for {t}: {e}")

        if not recommendations:
            return jsonify(success=False, message="No personalized results found."), 404

        # ✅ Normalize similarity → match_percent
        max_sim = max(r["similarity"] for r in recommendations) or 1
        for r in recommendations:
            r["match_percent"] = round((r["similarity"] / max_sim) * 100, 1)
            if not r.get("poster"):
                r["poster"] = "https://via.placeholder.com/500x750?text=Poster+Unavailable"

        recommendations = sorted(recommendations, key=lambda x: x["match_percent"], reverse=True)[:20]

        return jsonify(success=True, results=recommendations), 200

    except Exception as e:
        current_app.logger.exception("Error generating personalized recommendations")
        return jsonify(success=False, message="Server error", error=str(e)), 500
