import json

from flask import request, jsonify

import app.service.user_service as user_service
from app.clients.postgres_client import app
from app.service import crossword_service


@app.route('/api/solver', methods=['POST'])
def solve():
    file = request.files['image']

    content = json.load(request.files['data'])

    user_id = content['user_id']
    crossword_name = content['crossword_name']
    timestamp = content['timestamp']

    user = user_service.get_user_by_user_id(user_id)
    if user is None:
        return jsonify({'error': 'User with given id does not exist'}), 401

    crossword_info = crossword_service.get_crossword_info_by_crossword_name_and_user_id(user.user_id, crossword_name)
    if crossword_info is not None:
        return jsonify({'error': 'Crossword with this name already exist'}), 400

    crossword_task = crossword_service.add_crossword_task(file.stream, user_id, crossword_name, timestamp)
    return jsonify({'info': f'photo has been received and saved with id: {crossword_task.crossword_info_id}'}), 200
