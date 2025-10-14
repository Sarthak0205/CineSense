# backend/routes/auth_routes.py
from flask import Blueprint, request, jsonify, current_app
import bcrypt
from datetime import datetime
from pymongo.errors import DuplicateKeyError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    db = current_app.db
    data = request.json or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')
    name = data.get('name') or ''
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    # safe to store hashed as utf-8 string
    user_doc = {
        'email': email,
        'password': hashed.decode('utf-8'),
        'name': name,
        'created_at': datetime.utcnow()
    }
    try:
        res = db.users.insert_one(user_doc)
    except DuplicateKeyError:
        return jsonify({'error': 'Email already registered'}), 409

    return jsonify({'message': 'User registered', 'user': {'id': str(res.inserted_id), 'email': email, 'name': name}}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    db = current_app.db
    data = request.json or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = db.users.find_one({'email': email})
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    stored_hash = user.get('password', '')
    try:
        ok = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except Exception:
        ok = False
    if not ok:
        return jsonify({'error': 'Invalid credentials'}), 401

    return jsonify({'message': 'Login successful', 'user': {'id': str(user['_id']), 'email': user['email'], 'name': user.get('name','')}}), 200
