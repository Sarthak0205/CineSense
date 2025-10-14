from flask import Blueprint, request, jsonify, current_app

rec_bp = Blueprint('rec', __name__)

@rec_bp.route('/recommend', methods=['POST'])
def get_recommendations():
    data = request.json
    title = data.get('title', '')
    content_type = data.get('type', None)
    
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    model = current_app.clustering_model
    recommendations = model.get_recommendations(title, content_type)
    
    if not recommendations:
        return jsonify({'message': 'No recommendations found', 'data': []}), 200
    
    return jsonify({
        'message': 'Recommendations found',
        'data': recommendations
    }), 200

@rec_bp.route('/browse/<content_type>', methods=['GET'])
def browse_content(content_type):
    model = current_app.clustering_model
    items = model.get_all_items(content_type if content_type != 'all' else None)
    
    return jsonify({
        'message': f'Found {len(items)} items',
        'data': items
    }), 200