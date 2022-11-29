import json

import shortuuid
from flask import request, jsonify
from flask import send_file

from app.clients.postgres_client import app, db
from app.model.crossword_clue import CrosswordClue
from app.processing.crossword_manager import solve_crossword


@app.route("/api/health", methods=["GET"])
def hello():
    return "Hello world"


@app.route("/api/solve", methods=["POST"])
def solve():
    file = request.files['image']
    user_id = "USER_ID"

    file_path = solve_crossword(file.stream, user_id)

    return send_file(file_path, mimetype='image/gif')


@app.route("/api/register", methods=["GET"])
def register():
    user_id = shortuuid.uuid()
    print(user_id)
    # TODO save user in database
    return jsonify({'user_id': str(user_id)})


@app.route("/api/login", methods=["POST"])
def login():
    content = request.json
    user_id = content['user_id']

    print(user_id)

    # TODO check if user_id exist in database
    user_exists = len(user_id) == 22
    if user_exists:
        return jsonify({'user_id': user_id})
    else:
        return jsonify({'error': "User with given id does not exist"})


@app.route("/api/crossword-clue", methods=["GET"])
def get_all_crossword_clues():
    crossword_clues = db.session.query(CrosswordClue).all()
    return json.dumps([crossword_clue.serialize for crossword_clue in crossword_clues])


@app.route("/api/crossword-clue", methods=["PUT"])
def add_crossword_clue():
    try:
        content = request.json
        user_id = content['user_id']
        # TODO check if user_id exist in database

        answers = content['answer']
        if len(answers) == 0:
            return "Answers for question cannot be empty", 400

        question = content['question']
        crossword_clue = get_crossword_clue_by_question(question)
        if crossword_clue is not None:
            crossword_clue.answers = answers
            db.session.commit()
            return crossword_clue.serialize, 200

        crossword_clue_to_add = CrosswordClue(
            user_id=user_id,
            question=question,
            answers=answers
        )
        db.session.add(crossword_clue_to_add)
        db.session.commit()

        return crossword_clue_to_add.serialize, 201
    except Exception as e:
        return str(e)


def get_crossword_clue_by_question(question):
    return db.session \
        .query(CrosswordClue) \
        .filter(CrosswordClue.question == question) \
        .one_or_none()


if __name__ == "__main__":
    # start flask app
    app.run(host="0.0.0.0", port=5326)
