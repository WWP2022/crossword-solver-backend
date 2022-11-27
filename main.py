from flask import Flask, request, send_file

from app.processing.crossword_manager import solve_crossword

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


if __name__ == "__main__":
    # start flask app
    app.run(host="0.0.0.0", port=5326)
