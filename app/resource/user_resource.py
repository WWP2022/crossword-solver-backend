from flask import request, jsonify

import app.service.user_service as user_service
import app.service.crossword_service as crossword_service
from app.clients.postgres_client import app


@app.route('/api/register', methods=['POST'])
def register():
    user = user_service.register_new_user()
    return user.serialize, 201


@app.route('/api/login', methods=['POST'])
def login():
    content = request.json
    user_id = content['user_id']

    user = user_service.get_user_by_user_id(user_id)
    if user is None:
        return jsonify({'error': 'User with given id does not exist'}), 401

    return user.serialize, 200


@app.route('/api/user/info', methods=['GET'])
def user_info():
    args = request.args
    user_id = args.get('user_id')
    if user_id is None:
        return jsonify({'error': 'user_id is obligatory query param'}), 400

    user = user_service.get_user_by_user_id(user_id)
    if user is None:
        return jsonify({'error': 'User with given id does not exist'}), 401

    return jsonify({
        'user_id': user_id,
        'created': str(user.created),
        'all_crosswords_number': str(crossword_service.get_number_of_all_crossword_by_user_id(user_id)),
    }), 200
