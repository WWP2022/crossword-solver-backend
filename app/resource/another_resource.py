from flask import request, jsonify
from flask import send_file

from app.clients.postgres_client import app
from app.processing.crossword_manager import solve_crossword
from app.service.user_service import get_user_by_user_id, register_new_user


@app.route('/api/health', methods=['GET'])
def hello():
    return 'Hello world'


@app.route('/api/solve', methods=['POST'])
def solve():
    file = request.files['image']
    user_id = 'USER_ID'

    file_path = solve_crossword(file.stream, user_id)

    return send_file(file_path, mimetype='image/gif')


@app.route('/api/register', methods=['POST'])
def register():
    user = register_new_user()
    return user.serialize, 201


@app.route('/api/login', methods=['POST'])
def login():
    content = request.json
    user_id = content['user_id']

    user = get_user_by_user_id(user_id)
    if user is None:
        return jsonify({'error': 'User with given id does not exist'}), 401

    return user.serialize, 200
