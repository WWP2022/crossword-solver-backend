from flask import Flask, request, send_file, jsonify

from app.processing.crossword_manager import solve_crossword
import shortuuid
import random

app = Flask(__name__)


@app.route("/api/hello", methods=["GET"])
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

    # TODO Check if user_id exist in database
    user_exists = len(user_id) == 22
    if user_exists:
        return jsonify({'user_id': user_id})
    else:
        return jsonify({'error': "User with given id does not exist"})


if __name__ == "__main__":
    # start flask app
    app.run(host="0.0.0.0", port=5326)
