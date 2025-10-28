# backend/routes/auth_routes.py

from flask import Blueprint, request, jsonify, current_app
from db import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import datetime
import re
from bson import ObjectId

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# ───────────────────────────────
# Email validation + index setup
# ───────────────────────────────
EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

def ensure_email_index():
    """Ensure unique index on 'email' field"""
    try:
        mongo.db.users.create_index("email", unique=True)
    except Exception:
        pass  # already exists

@auth_bp.record_once
def on_load(state):
    """Run once when blueprint is registered"""
    try:
        ensure_email_index()
    except Exception as e:
        current_app.logger.warning(f"Index creation failed: {e}")

# ───────────────────────────────
# Register endpoint
# ───────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not email or not password:
        return jsonify({"success": False, "message": "username, email and password required"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"success": False, "message": "invalid email"}), 400
    if len(password) < 6:
        return jsonify({"success": False, "message": "password must be at least 6 characters"}), 400

    users = mongo.db.users
    if users.find_one({"email": email}):
        return jsonify({"success": False, "message": "email already registered"}), 409

    pw_hash = generate_password_hash(password)
    user_doc = {
        "username": username,
        "email": email,
        "password": pw_hash,
        "favorites": {"movies": [], "series": [], "anime": []},
        "created_at": datetime.datetime.utcnow()
    }

    try:
        res = users.insert_one(user_doc)
        return jsonify({
            "success": True,
            "message": "user created",
            "user_id": str(res.inserted_id)
        }), 201
    except Exception as e:
        current_app.logger.exception("User creation failed")
        return jsonify({"success": False, "message": "internal server error"}), 500

# ───────────────────────────────
# Login endpoint
# ───────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"success": False, "message": "email and password required"}), 400

    users = mongo.db.users
    user = users.find_one({"email": email})
    if not user or not check_password_hash(user.get("password", ""), password):
        return jsonify({"success": False, "message": "invalid credentials"}), 401

    expires_seconds = int(current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    token = create_access_token(
        identity=str(user["_id"]),
        expires_delta=datetime.timedelta(seconds=expires_seconds)
    )

    return jsonify({
        "success": True,
        "access_token": token,
        "username": user.get("username"),
        "email": user.get("email")
    }), 200

# ───────────────────────────────
# Protected route to get profile
# ───────────────────────────────
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    uid = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(uid)})
    if not user:
        return jsonify({"success": False, "message": "user not found"}), 404

    profile = {
        "username": user.get("username"),
        "email": user.get("email"),
        "favorites": user.get("favorites", {"movies": [], "series": [], "anime": []}),
        "created_at": user.get("created_at")
    }
    return jsonify({"success": True, "profile": profile}), 200
