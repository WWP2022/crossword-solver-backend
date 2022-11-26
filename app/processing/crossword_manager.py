from PIL import Image

from app.hardcoded import hardcoded_crossword
from app.processing.extract_crossword import extract_crossword
from app.processing.result_image import create_result_image


def solve_crossword(stream, user_id):
    img = Image.open(stream)
    img = img.convert("RGB")

    tmp_image_path = "/tmp/test_unprocessed.jpg"
    img.save(tmp_image_path, quality=100)

    # TODO Now we use hardcoded_crossword because ocr is not working
    extract_crossword(tmp_image_path)
    crossword = hardcoded_crossword
    crossword.solve()
    # crossword.print_result()

    create_result_image(crossword, "app/assets/crossword_examples/big-panoram.png")

    return "tmp/processed_image.png"