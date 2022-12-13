import os
from pathlib import Path

from PIL import ImageFont, ImageDraw, Image


def draw_letter_on_image(file_name, letter):
    image = Image.open(file_name)
    draw = ImageDraw.Draw(image)
    txt = letter
    fontsize = 1  # starting font size

    W, H = image.size

    # portion of image width you want text width to be
    blank = Image.new('RGB', (W, H))

    font_path = str(Path(os.path.realpath(__file__)).parent.parent) + "/assets/fonts/FreeSans.ttf"

    font = ImageFont.truetype(font_path, fontsize)

    while (font.getsize(txt)[0] < blank.size[0]) and (font.getsize(txt)[1] < blank.size[1]):
        # iterate until the text size is just larger than the criteria
        fontsize += 1
        font = ImageFont.truetype(font_path, fontsize)

    # optionally de-increment to be sure it is less than criteria
    fontsize -= 40
    font = ImageFont.truetype(font_path, fontsize)

    w, h = draw.textsize(txt, font=font)

    # print 'final font size',fontsize
    draw.text(((W - w) / 2, (H - h) / 2), txt, font=font, fill="black")  # put the text on the image
    image.save(file_name)  # save it


def create_result_image(crossword, base_image_path, unprocessed_image_path):
    image = Image.open(unprocessed_image_path)
    new_im = Image.new('RGB', image.size)

    curr_x, curr_y = (0, 0)
    for i in range(crossword.row_number):
        for j in range(crossword.col_number):
            path = base_image_path + str(i) + "_" + str(j) + ".png"
            if crossword.data[i][j] not in ["#", "."]:
                draw_letter_on_image(path, crossword.data[i][j])
            image = Image.open(path)
            new_im.paste(image, (curr_x, curr_y))
            curr_x += image.width

        curr_x = 0
        curr_y += image.height

    new_im.save(base_image_path + "processed.png")

    return base_image_path + "processed.png"
