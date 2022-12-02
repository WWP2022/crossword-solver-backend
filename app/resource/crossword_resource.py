from flask import request, jsonify, send_file

import app.service.crossword_service as crossword_service
import app.service.user_service as user_service
from app.clients.postgres_client import app
from app.model.database.crossword_info import CrosswordStatus


@app.route('/api/crossword/status', methods=['GET'])
def status():
    args = request.args
    user_id = args.get('user_id')
    if user_id is None:
        return jsonify({'error': 'user_id is obligatory query param'}), 400

    crossword_name = args.get('crossword_name')
    if crossword_name is None:
        return jsonify({'error': 'crossword_name is obligatory query param'}), 400

    user = user_service.get_user_by_user_id(user_id)
    if user is None:
        return jsonify({'error': 'User with given id does not exist'}), 401

    crossword_info = crossword_service.get_crossword_info_by_crossword_name_and_user_id(user, crossword_name)
    if crossword_info is None:
        return jsonify({'error': 'Crossword does not exist'}), 404

    return jsonify({'status': crossword_info.status}), 200


@app.route('/api/crossword', methods=['PATCH'])
def update_crossword():
    content = request.json
    user_id = content['user_id']
    crossword_name = content['crossword_name']
    is_correct = content['is_accepted']

    user = user_service.get_user_by_user_id(user_id)
    if user is None:
        return jsonify({'error': 'User with given id does not exist'}), 401

    crossword_info = crossword_service.get_crossword_info_by_crossword_name_and_user_id(user_id, crossword_name)
    if crossword_info is None:
        return jsonify({'error': 'Crossword with this name not exist'}), 404

    if crossword_info.status == CrosswordStatus.SOLVED_WAITING.value:
        crossword_info = crossword_service.update_crossword(crossword_info, crossword_name, is_correct)
        return jsonify({
            "user_id": user_id,
            "crossword_name": crossword_info.crossword_name,
            "status": crossword_info.status
        }), 201

    new_crossword_name = content['new_crossword_name']
    crossword_info = crossword_service.update_crossword(crossword_info, new_crossword_name, is_correct)

    return jsonify({
        "user_id": user_id,
        "crossword_name": crossword_info.crossword_name,
        "status": crossword_info.status
    }), 201


@app.route('/api/crossword', methods=['GET'])
def get_solved_crossword():
    args = request.args

    user_id = args.get('user_id')
    if user_id is None:
        return jsonify({'error': 'user_id is obligatory query param'}), 400

    user = user_service.get_user_by_user_id(user_id)
    if user is None:
        return jsonify({'error': 'User with given id does not exist'}), 401

    crossword_name = args.get('crossword_name')
    image_path = crossword_service.get_crossword_processed_image(user_id, crossword_name)

    if image_path is None:
        return jsonify({'error': 'Crossword does not exist'}), 404

    return send_file(image_path, mimetype='image/gif'), 200


@app.route('/api/crossword/all', methods=['GET'])
def get_solved_crossword_names_and_timestamps():
    args = request.args

    user_id = args.get('user_id')
    if user_id is None:
        return jsonify({'error': 'user_id is obligatory query param'}), 400

    user = user_service.get_user_by_user_id(user_id)
    if user is None:
        return jsonify({'error': 'User with given id does not exist'}), 401

    crossword_data = crossword_service.get_crossword_processed_images_names_and_timestamps_by_user_id(user_id)

    return crossword_data, 200
