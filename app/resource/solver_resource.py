import json

from flask import request, jsonify

import app.service.user_service as user_service
from app.clients.postgres_client import app
from app.service import crossword_service


@app.route('/api/solver', methods=['POST'])
def solve():
    file = request.files['image']
    user_id = request.form.get('user_id')
    timestamp = request.form.get('timestamp')

    user = user_service.get_user_by_user_id(user_id)
    if user is None:
        return jsonify({'error': 'User with given id does not exist'}), 401

    user = user_service.update_number_of_crosswords(user_id, user.sent_crosswords + 1)

    default_crossword_name = crossword_service.get_default_name(user.user_id)

    crossword_task = crossword_service.add_crossword_task(
        file.stream,
        user.user_id,
        default_crossword_name,
        timestamp
    )

    return jsonify(
        {'id': crossword_task.crossword_info_id,
         'crossword_name': default_crossword_name}
    ), 200
