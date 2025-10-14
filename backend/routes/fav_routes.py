# backend/routes/fav_routes.py
from flask import Blueprint, request, jsonify, current_app
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from bson import ObjectId

fav_bp = Blueprint('fav', __name__)

@fav_bp.route('/favorites', methods=['POST'])
def add_favorite():
    db = current_app.db
    data = request.json or {}
    user_id = data.get('user_id')
    movie = data.get('movie')
    if not user_id or not movie or not movie.get('title'):
        return jsonify({'error': 'user_id and movie with title are required'}), 400

    favorite = {
        'user_id': str(user_id),
        'movie_id': movie.get('title'),
        'movie': movie,
        'created_at': datetime.utcnow()
    }
    try:
        db.favorites.insert_one(favorite)
        return jsonify({'message': 'Added to favorites'}), 201
    except DuplicateKeyError:
        return jsonify({'message': 'Already in favorites'}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to add favorite', 'detail': str(e)}), 500

@fav_bp.route('/favorites/<user_id>', methods=['GET'])
def get_favorites(user_id):
    db = current_app.db
    favorites = list(db.favorites.find({'user_id': str(user_id)}))
    for fav in favorites:
        fav['_id'] = str(fav['_id'])
    return jsonify({'message': f'Found {len(favorites)} favorites', 'data': favorites}), 200

@fav_bp.route('/favorites/<user_id>', methods=['DELETE'])
def remove_favorite(user_id):
    db = current_app.db
    movie_title = request.json.get('movie_title')
    if not movie_title:
        return jsonify({'error': 'movie_title required in JSON body'}), 400
    res = db.favorites.delete_one({'user_id': str(user_id), 'movie_id': movie_title})
    if res.deleted_count:
        return jsonify({'message': 'Removed from favorites'}), 200
    return jsonify({'message': 'Not found'}), 404
