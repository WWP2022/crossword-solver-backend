from PIL import ImageFont, ImageDraw, Image

from app.clients.minio_client import put_processed_image


def draw_letter_on_image(file_name, letter):
    image = Image.open(file_name)
    draw = ImageDraw.Draw(image)
    txt = letter
    fontsize = 1  # starting font size

    W, H = image.size

    # portion of image width you want text width to be
    blank = Image.new('RGB', (W, H))

    font = ImageFont.truetype("app/assets/fonts/default.ttf", fontsize)

    while (font.getsize(txt)[0] < blank.size[0]) and (font.getsize(txt)[1] < blank.size[1]):
        # iterate until the text size is just larger than the criteria
        fontsize += 1
        font = ImageFont.truetype("app/assets/fonts/default.ttf", fontsize)

    # optionally de-increment to be sure it is less than criteria
    fontsize -= 40
    font = ImageFont.truetype("app/assets/fonts/default.ttf", fontsize)

    w, h = draw.textsize(txt, font=font)

    # print 'final font size',fontsize
    draw.text(((W - w) / 2, (H - h) / 2), txt, font=font, fill="black")  # put the text on the image
    image.save(file_name)  # save it


def create_result_image(crossword, path):
    image = Image.open(path)
    new_im = Image.new('RGB', image.size)

    curr_x, curr_y = (0, 0)
    for i in range(crossword.row_number):
        for j in range(crossword.col_number):
            path = "tmp/" + str(i) + "_" + str(j) + ".png"
            if crossword.data[i][j] != "#":
                draw_letter_on_image(path, crossword.data[i][j])
            image = Image.open(path)
            new_im.paste(image, (curr_x, curr_y))
            curr_x += image.width

        curr_x = 0
        curr_y += image.height

    new_im.save("tmp/processed_image.png")

    put_processed_image("USER_ID", "tmp/processed_image.png")
