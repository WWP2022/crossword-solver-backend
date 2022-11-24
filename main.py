from flask import Flask, request, send_file
from PIL import Image

from app.processing_image.extract_crossword import extract_crossword
from app.hardcoded import hardcoded_crossword
from app.processing_image.result_image import create_result_image

app = Flask(__name__)


@app.route("/api/process-image", methods=["POST"])
def process_image():
    file = request.files['image']

    img = Image.open(file.stream)
    img = img.convert("RGB")

    tmp_image = "/tmp/test_unprocessed.jpg"
    img.save(tmp_image, quality=100)

    # TODO Now we use hardcoded_crossword because ocr is not working
    extract_crossword(tmp_image)
    crossword = hardcoded_crossword
    crossword.solve()
    # crossword.print_result()

    create_result_image(crossword, "app/assets/crossword_examples/big-panoram.png")

    return send_file("tmp/processed_image.png", mimetype='image/gif')


if __name__ == "__main__":
    # start flask app
    app.run(host="0.0.0.0", port=5000)
