import json

from flask import request, jsonify

from app.clients.postgres_client import app
from app.repository.crossword_clue_repository import get_crossword_clues_by_user_id, \
    save_crossword_clue, delete_crossword_clue_by_question_and_user_id
from app.service.user_service import get_user_by_user_id


@app.route('/api/crossword-clue', methods=['DELETE'])
def delete_crossword_clue():
    args = request.args
    user_id = args.get('user_id')
    if user_id is None:
        return jsonify({'error': 'user_id is obligatory query param'}), 400

    question = args.get('question')
    if question is None:
        return jsonify({'error': 'question is obligatory query param'}), 400

    crossword_clue = delete_crossword_clue_by_question_and_user_id(question, user_id)
    return crossword_clue.serialize, 204


@app.route('/api/crossword-clue', methods=['GET'])
def get_all_crossword_clues():
    args = request.args
    user_id = args.get('user_id')
    if user_id is None:
        return jsonify({'error': 'user_id is obligatory query param'}), 400

    crossword_clues = get_crossword_clues_by_user_id(user_id)
    return [crossword_clue.serialize for crossword_clue in crossword_clues]


@app.route('/api/crossword-clue', methods=['PUT'])
def add_crossword_clue():
    try:
        content = request.json
        user_id = content['user_id']

        user = get_user_by_user_id(user_id)
        if user is None:
            return jsonify({'error': 'User with given id does not exist'}), 401

        answers = json.dumps(content['answers'])
        if len(answers) == 0:
            return jsonify({'error': 'Answers for question cannot be empty'}), 400

        question = content['question']
        crossword_clue = save_crossword_clue(question, answers, user_id)

        return crossword_clue.serialize, 201
    except Exception as e:
        return str(e)
