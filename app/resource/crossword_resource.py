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

    crossword_id = args.get('crossword_id')
    if crossword_id is None:
        return jsonify({'error': 'crossword_id is obligatory query param'}), 400

    user = user_service.get_user_by_user_id(user_id)
    if user is None:
        return jsonify({'error': 'User with given id does not exist'}), 401

    crossword_info = crossword_service.get_crossword_info_by_crossword_id(int(crossword_id))
    if crossword_info is None:
        return jsonify({'error': 'Crossword does not exist'}), 400

    return jsonify({'status': crossword_info.status, 'message': crossword_info.solving_message}), 200


@app.route('/api/crossword', methods=['PATCH'])
def update_crossword():
    content = request.json
    user_id = content['user_id']
    crossword_id = int(content['crossword_id'])
    crossword_name = content['crossword_name'] if 'crossword_name' in content.keys() else None
    is_accepted = content['is_accepted'] if 'is_accepted' in content.keys() else True

    user = user_service.get_user_by_user_id(user_id)
    if user is None:
        return jsonify({'error': 'User with given id does not exist'}), 401

    crossword_info = crossword_service.get_crossword_info_by_crossword_id(crossword_id)
    if crossword_info is None:
        return jsonify({'error': 'Crossword with this id not exist'}), 404

    if crossword_name is not None and crossword_service.is_crossword_name_exist(user_id, crossword_name):
        return jsonify({'error': 'Crossword with new name has already exist'}), 400

    if crossword_info.status == CrosswordStatus.SOLVED_WAITING.value or crossword_name is not None:
        crossword_info = crossword_service.update_crossword(crossword_info, crossword_name, is_accepted)
        return jsonify({
            "user_id": user_id,
            "crossword_name": crossword_info.crossword_name,
            "status": crossword_info.status
        }), 201

    return jsonify({'error': 'You can only change crossword_name'})


@app.route('/api/crossword', methods=['GET'])
def get_solved_crossword():
    args = request.args

    user_id = args.get('user_id')
    if user_id is None:
        return jsonify({'error': 'user_id is obligatory query param'}), 400

    user = user_service.get_user_by_user_id(user_id)
    if user is None:
        return jsonify({'error': 'User with given id does not exist'}), 401

    crossword_id = int(args.get('crossword_id'))
    image_path = crossword_service.get_crossword_processed_image(user_id, crossword_id)

    if image_path is None:
        return jsonify({'error': 'Crossword does not exist'}), 404

    return send_file(image_path, mimetype='image/gif'), 200


@app.route('/api/crossword', methods=['DELETE'])
def delete_crossword():
    args = request.args
    user_id = args.get('user_id')
    if user_id is None:
        return jsonify({'error': 'user_id is obligatory query param'}), 400

    crossword_id = args.get('crossword_id')
    if crossword_id is None:
        return jsonify({'error': 'crossword_id is obligatory query param'}), 400

    user = user_service.get_user_by_user_id(user_id)
    if user is None:
        return jsonify({'error': 'User with given id does not exist'}), 401

    crossword_info = crossword_service.get_crossword_info_by_crossword_id(int(crossword_id))
    if crossword_info is None:
        return jsonify({'error': 'Crossword with given id does not exist'}), 404

    crossword_info = crossword_service.delete_crossword(crossword_info)

    return jsonify({"crossword_id": crossword_info.id,
                    "crossword_name": crossword_info.crossword_name,
                    "timestamp": crossword_info.timestamp}), 204


@app.route('/api/crossword/all', methods=['GET'])
def get_solved_crossword_ids_names_and_timestamps():
    args = request.args

    user_id = args.get('user_id')
    if user_id is None:
        return jsonify({'error': 'user_id is obligatory query param'}), 400

    user = user_service.get_user_by_user_id(user_id)
    if user is None:
        return jsonify({'error': 'User with given id does not exist'}), 401

    crossword_data = crossword_service.get_crossword_processed_images_ids_names_and_timestamps_by_user_id(user_id)

    return jsonify(crossword_data), 200
