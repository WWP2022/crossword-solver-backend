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
