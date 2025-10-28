from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from db import mongo

favorites_bp = Blueprint("favorites", __name__, url_prefix="/api/favorites")


# ✅ Utility: Normalize type
def normalize_type(t):
    t = (t or "").lower().strip()
    if "anime" in t:
        return "anime"
    elif t in ["tv", "series", "show"]:
        return "series"
    else:
        return "movies"


# ✅ Get all favorites for the logged-in user (grouped by category)
@favorites_bp.route("/", methods=["GET"])
@jwt_required()
def get_favorites():
    try:
        uid = get_jwt_identity()
        user = mongo.db.users.find_one({"_id": ObjectId(uid)}, {"favorites": 1})
        if not user:
            return jsonify(success=False, message="User not found"), 404

        fav_data = user.get("favorites", {})

        # 🔹 Handle old users where favorites was a list instead of dict
        grouped = {"movies": [], "series": [], "anime": []}
        if isinstance(fav_data, list):
            for f in fav_data:
                ftype = normalize_type(f.get("type"))
                grouped[ftype].append(f)
        elif isinstance(fav_data, dict):
            for key in ["movies", "series", "anime"]:
                grouped[key] = fav_data.get(key, [])
        else:
            grouped = {"movies": [], "series": [], "anime": []}

        return jsonify(success=True, favorites=grouped), 200

    except Exception as e:
        current_app.logger.exception("Error fetching favorites")
        return jsonify(success=False, message="Server error", error=str(e)), 500


# ✅ Add a favorite (stored in correct category)
@favorites_bp.route("/add", methods=["POST"])
@jwt_required()
def add_favorite():
    try:
        uid = get_jwt_identity()
        data = request.get_json() or {}

        title = data.get("title")
        poster = data.get("poster")
        type_ = normalize_type(data.get("type", "movies"))

        if not title:
            return jsonify(success=False, message="Title required"), 400

        user = mongo.db.users.find_one({"_id": ObjectId(uid)})
        if not user:
            return jsonify(success=False, message="User not found"), 404

        # ✅ Ensure correct structure in DB
        if not isinstance(user.get("favorites"), dict):
            mongo.db.users.update_one(
                {"_id": ObjectId(uid)},
                {"$set": {"favorites": {"movies": [], "series": [], "anime": []}}},
            )
            user["favorites"] = {"movies": [], "series": [], "anime": []}

        # ✅ Check for duplicates in that category
        existing = next(
            (f for f in user["favorites"].get(type_, []) if f.get("title") == title),
            None,
        )
        if existing:
            return jsonify(success=False, message="Already in favorites"), 400

        favorite_item = {
            "_id": str(ObjectId()),
            "title": title,
            "poster": poster,
            "type": type_,
        }

        mongo.db.users.update_one(
            {"_id": ObjectId(uid)},
            {"$push": {f"favorites.{type_}": favorite_item}},
        )

        return jsonify(success=True, message=f"Added to {type_} favorites"), 200

    except Exception as e:
        current_app.logger.exception("Error adding favorite")
        return jsonify(success=False, message="Server error", error=str(e)), 500


# ✅ Remove a favorite by ID
@favorites_bp.route("/remove/<fid>", methods=["DELETE"])
@jwt_required()
def remove_favorite(fid):
    try:
        uid = get_jwt_identity()

        # Remove from all 3 categories (safe cleanup)
        mongo.db.users.update_one(
            {"_id": ObjectId(uid)},
            {
                "$pull": {
                    "favorites.movies": {"_id": fid},
                    "favorites.series": {"_id": fid},
                    "favorites.anime": {"_id": fid},
                }
            },
        )

        return jsonify(success=True, message="Removed from favorites"), 200
    except Exception as e:
        current_app.logger.exception("Error removing favorite")
        return jsonify(success=False, message=str(e)), 500
