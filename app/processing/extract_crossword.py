import os
from pathlib import Path
from time import time
from warnings import filterwarnings

import cv2
import numpy as np
import pandas as pd
import pytesseract
import torch
import torchvision.transforms as transforms
from torch.autograd import Variable

from app.model.crossword import Crossword
from app.model.crossword_node import CrosswordNode
from app.model.database.crossword_info import CrosswordSolvingMessage
from app.model.ml.pytorchModel import Net
from app.utils import spell_corrector
from app.utils.docker_logs import get_logger

logger = get_logger('extract_crossword')

filterwarnings('ignore')

category_mapper = {
    0: 'down',
    1: 'down_right',
    2: 'empty',
    3: 'left_down',
    4: 'right',
    5: 'right_and_down',
    6: 'right_down',
    7: 'text',
    8: 'up_right'
}


def calc_coordinates(line):
    rho, theta = line.reshape(-1)
    a = np.cos(theta)
    b = np.sin(theta)
    x0 = a * rho
    y0 = b * rho
    x1 = int(x0 + 100000 * (-b))
    y1 = int(y0 + 100000 * a)
    x2 = int(x0 - 100000 * (-b))
    y2 = int(y0 - 100000 * a)

    return x1, y1, x2, y2


def calc_tangent(x1, y1, x2, y2):
    if (y2 - y1) != 0:
        return abs((x2 - x1) / (y2 - y1))
    return 1000


def get_lines(image, filter=True):
    """
    The method finds each crossword cell with Lines
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 90, 100, apertureSize=3)
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    kernel = np.ones((5, 5), np.uint8)
    edges = cv2.erode(edges, kernel, iterations=1)

    # find lines on the preprocessed image u|sing Hough Transform
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 275)

    # This image not show all lines, we have also correct_lines
    # cv2.imwrite('edges.jpg', edges)
    if lines is None:
        return None

    # calculate how many horizontal lines were found
    tot = 0
    for line in lines:
        x1, y1, x2, y2 = calc_coordinates(line)

        tan = calc_tangent(x1, y1, x2, y2)
        if tan > 1000:
            tot += 1

    boundaryLines = np.asarray(
        [[0, 0], [1, 1.5707964e+00], [image.shape[1], 0], [image.shape[0], 1.5707964e+00]]).reshape(-1, 1, 2)
    lines = list(np.concatenate([np.asarray(lines), boundaryLines], axis=0))
    # remove redundant lines which do not  fit into the crossword pattern
    if filter:
        rho_threshold = image.shape[0] / (tot + 1)
        theta_threshold = 0.01

        # how many lines are similar to a given one
        similar_lines = {i: [] for i in range(len(lines))}
        for i in range(len(lines)):
            for j in range(len(lines)):
                if i == j:
                    continue

                rho_i, theta_i = lines[i][0]
                rho_j, theta_j = lines[j][0]
                if abs(rho_i - rho_j) < rho_threshold and abs(theta_i - theta_j) < theta_threshold:
                    similar_lines[i].append(j)

        # ordering the INDECES of the lines by how many are similar to them
        indices = [i for i in range(len(lines))]
        indices.sort(key=lambda x: len(similar_lines[x]))

        # line flags is the base for the filtering
        line_flags = len(lines) * [True]
        for i in range(len(lines) - 1):
            if not line_flags[indices[
                i]]:  # if we already disregarded the ith element in the ordered list then we don't care (we will not delete anything based on it and we will never reconsider using this line again)
                continue

            for j in range(i + 1, len(lines)):  # we are only considering those elements that had less similar line
                if not line_flags[indices[j]]:  # and only if we have not disregarded them already
                    continue

                rho_i, theta_i = lines[indices[i]][0]
                rho_j, theta_j = lines[indices[j]][0]
                if abs(rho_i - rho_j) < rho_threshold and abs(theta_i - theta_j) < theta_threshold:
                    line_flags[
                        indices[j]] = False  # if it is similar and have not been disregarded yet then drop it now

    # print('number of Hough lines:', len(lines))

    filtered_lines = []

    if filter:
        for i in range(len(lines)):  # filtering
            if line_flags[i]:
                filtered_lines.append(lines[i])

        # print('Number of filtered lines:', len(filtered_lines))
    else:
        filtered_lines = lines

    # draw the lines on the image and mask and save them
    mask = np.zeros_like(image)
    final_lines = []
    for line in filtered_lines:
        x1, y1, x2, y2 = calc_coordinates(line)
        tan = calc_tangent(x1, y1, x2, y2)
        if tan > 1000 or tan == 0:
            # if you want see lines on images uncomment this
            # cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.line(mask, (x1, y1), (x2, y2), (0, 0, 255), 2)
            final_lines.append(line)

    # TODO useful images to see processing
    # cv2.imwrite('hough.jpg', image)
    # cv2.imwrite('mask.jpg', mask)

    return final_lines


def intersection(line1, line2):
    """Finds the intersection of two lines given in Hesse normal form.

    Returns closest integer pixel locations.
    See https://stackoverflow.com/a/383527/5087436
    """
    rho1, theta1 = line1
    rho2, theta2 = line2
    A = np.array([
        [np.cos(theta1), np.sin(theta1)],
        [np.cos(theta2), np.sin(theta2)]
    ])
    b = np.array([[rho1], [rho2]])
    x0, y0 = np.linalg.solve(A, b)
    x0, y0 = int(np.round(x0)), int(np.round(y0))
    return [[x0, y0]]


def segmented_intersections(lines):
    """Finds the intersections between groups of lines."""

    intersections = []
    for i, group in enumerate(lines[:-1]):
        for next_group in lines[i + 1:]:
            for line1 in group:
                for line2 in next_group:
                    x11, y11, x21, y21 = calc_coordinates(line1)
                    x12, y12, x22, y22 = calc_coordinates(line2)

                    tan1 = calc_tangent(x11, y11, x21, y21)
                    tan2 = calc_tangent(x12, y12, x22, y22)

                    if abs(tan1 - tan2) > 0.5:
                        intersections.append(intersection(line1, line2))

    return intersections


def correct_lines(lines):
    """
    Adds some lines in case missing from standard methods
    """

    lineDists = pd.DataFrame(np.asarray(lines).reshape(-1, 2))
    lineDists.iloc[:, 1] = (lineDists.iloc[:, 1] > 0).apply(int)
    lineDists = lineDists.sort_values(by=[1, 0])
    lineDists.columns = ['rho', 'theta']
    lineDists['rho'] = lineDists['rho'].apply(int)
    newLines = []
    for value in lineDists['theta'].unique():
        curDists = lineDists[lineDists['theta'] == value]
        curDists['delta'] = curDists['rho'] - curDists['rho'].shift(1).fillna(0)

        med = np.median(curDists['delta'].values)
        for index, dist in enumerate(curDists['delta'].values):
            if dist > 1.5 * med:
                newLines.append(
                    np.array([(curDists.iloc[index - 1, 0] + curDists.iloc[index, 0]) // 2, value]).reshape(1, 2))
    return lines + newLines


def create_crops(intersections, image, base_image_path):
    # cut each cell separately and place it into the tmp folder
    try:
        os.mkdir(base_image_path)
    except:
        pass

    xs = sorted(np.unique(np.asarray(intersections)[:, 0, 0]))
    ys = sorted(np.unique(np.asarray(intersections)[:, 0, 1]))
    first_image_size = 0
    for i, x in enumerate(xs[:-1]):
        for j, y in enumerate(ys[:-1]):
            cropImage = image[y:ys[j + 1], x:xs[i + 1]]
            # TODO Może lepiej jest inaczej to sprawdzać jakoś, wcześniej wyłapać to?
            if first_image_size == 0:
                first_image_size = cropImage.size
            elif not (first_image_size * 0.7 < cropImage.size < first_image_size * 1.3):
                return CrosswordSolvingMessage.SOLVING_ERROR_CANNOT_CROPPED_IMAGES
            if not cropImage.any():
                return CrosswordSolvingMessage.SOLVING_ERROR_CANNOT_CROPPED_IMAGES
            cv2.imwrite(base_image_path + f'{j}_{i}.png', cropImage)

    return image


def ocr_core(filename):
    """
    This function will handle the core OCR processing of images.
    """

    image = cv2.imread(filename)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # wszystkie wartości powyżej 120 zamieniane na 255(biały) dla lepszego kontrastu
    image_2 = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY)[1]
    # TODO helpful image shows how look field before reading data
    # cv2.imwrite(filename, image_2)

    text = pytesseract.image_to_string(image_2, lang='pol', config=r'--psm 11')

    text_with_corrections = " ".join(text.split()).replace("- ", "")
    text_with_corrections = spell_corrector.correct_question(text_with_corrections)
    # TODO helpful print showing ocr on each field
    # print("Filename: " + filename + " Ocr: " + text_with_corrections)
    return text_with_corrections


def find_solution(data, i, j):
    """
    Finds direction and position of solution adjacent to the current text displacement
    """
    number_of_rows = data.shape[0]
    number_of_cols = data.shape[1]

    if number_of_cols > j + 1 and data.iloc[i, j + 1] == 'right':
        return ['right', i, j + 1]
    if number_of_rows > i + 1 and data.iloc[i + 1, j] == 'down':
        return ['down', i + 1, j]
    if j - 1 >= 0 and data.iloc[i, j - 1] == 'right_down':
        return ['down', i, j - 1]
    if number_of_cols > j + 1 and data.iloc[i, j + 1] == 'left_down':
        return ['down', i, j + 1]
    if i - 1 >= 0 and data.iloc[i - 1, j] == 'down_right':
        return ['right', i - 1, j]
    if number_of_rows > i + 1 and data.iloc[i + 1, j] == 'up_right':
        return ['right', i + 1, j]
    if number_of_cols > j + 1 and data.iloc[i, j + 1] == 'right_and_down':  # right
        return ['right', i, j + 1]
    if number_of_rows > i + 1 and data.iloc[i + 1, j] == 'right_and_down':  # down
        return ['down', i + 1, j]
    # 4 ifs beloaw are workaround for not proper divide field
    if number_of_rows > i + 1 and data.iloc[i + 1, j] == 'right':
        return ['right', i + 1, j]
    if i - 1 >= 0 and data.iloc[i - 1, j] == 'right':
        return ['right', i - 1, j]
    if number_of_cols > j + 1 and data.iloc[i, j + 1] == 'down':
        return ['down', i, j + 1]
    if j - 1 >= 0 and data.iloc[i, j - 1] == 'down':
        return ['down', i, j - 1]
    print(f'No arrow find for: [{i}, {j}]')
    return None


def find_length(data, solution):
    direction = solution[0]
    solution_start_row = solution[1]
    solution_start_column = solution[2]

    counter = 1
    number_of_rows = data.shape[0]
    number_of_cols = data.shape[1]

    if direction == "down":
        while (number_of_rows > solution_start_row + counter) and (
                data.iloc[solution_start_row + counter, solution_start_column] != "text"):
            counter += 1
        return counter

    else:
        while (number_of_cols > solution_start_column + counter) and (
                data.iloc[solution_start_row, solution_start_column + counter] != "text"):
            counter += 1
        return counter


def extract_crossword_to_model(data, base_image_path):
    crossword_nodes = []
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            if data.iloc[i, j] == 'text':
                solution = find_solution(data, i, j)
                if solution is None:
                    continue
                text = ocr_core(base_image_path + f'{i}_{j}.png')
                length = find_length(data, solution)
                crossword_nodes.append(
                    CrosswordNode(
                        definition=str(text),
                        position_of_definition=[i, j],
                        direction=solution[0],
                        solution_start_position=[solution[1], solution[2]],
                        length=length
                    )
                )
    crossword = Crossword(
        row_number=data.shape[0],
        col_number=data.shape[1],
        nodes=crossword_nodes
    )
    return crossword


def image_to_json(base_image_path, IMG_SHAPE=(64, 64), category_mapper={}):
    model_path = str(Path(os.path.realpath(__file__)).parent) + "/model.pt"

    if len(os.listdir(base_image_path)) == 1:
        return None
    print(os.listdir(base_image_path))

    matrix_size = sorted(list(map(lambda x: list(map(int, x.split('.')[0].split('_'))),
                                  [f for f in os.listdir(base_image_path) if "_" in f])))[-1]
    number_of_categories = len(category_mapper)
    property_matrix = np.zeros((matrix_size[0] + 1, matrix_size[1] + 1))
    textual_property_matrix = pd.DataFrame(np.zeros((matrix_size[0] + 1, matrix_size[1] + 1)))

    # load model
    net = Net(number_of_categories)
    net.load_state_dict(torch.load(model_path))
    net.eval()

    # define basic image transforms for preprocessing
    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.5,), std=(0.5,))
        ])

    for im in [f for f in os.listdir(base_image_path) if "_" in f]:
        img_path = base_image_path + im
        image = cv2.imread(img_path)

        idxs = list(map(int, im.split('.')[0].split('_')))
        image = cv2.resize(image, IMG_SHAPE)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = transform(image).reshape(1, 3, IMG_SHAPE[0], IMG_SHAPE[1])
        pred = net(Variable(image)).detach().numpy()
        property_matrix[idxs[0], idxs[1]] = np.argmax(pred)
        textual_property_matrix.iloc[idxs[0], idxs[1]] = category_mapper[np.argmax(pred)]
        # TODO helpful print showing prediction of field
        # print(img_path + " " + str(category_mapper[np.argmax(pred)]))

    return extract_crossword_to_model(textual_property_matrix, base_image_path)


def extract_crossword(unprocessed_image_path, base_image_path):
    t1 = time()

    image = cv2.imread(unprocessed_image_path)

    lines = get_lines(image, filter=True)

    if lines is None:
        logger.info(f'Error during processing: {CrosswordSolvingMessage.SOLVING_ERROR_NO_LINES.value}')
        return None, CrosswordSolvingMessage.SOLVING_ERROR_NO_LINES

    # corrects some missing lines
    lines = correct_lines(lines)

    # find line intersection points
    intersections = segmented_intersections(lines)

    # crop each cell to a separate file
    image = create_crops(intersections, image, base_image_path)

    if type(image) is CrosswordSolvingMessage:
        return None, image

    crossword = image_to_json(base_image_path, category_mapper=category_mapper)

    if crossword is None:
        logger.info(f'Error during processing: {CrosswordSolvingMessage.SOLVING_ERROR_NO_CROSSWORD.value}')
        return None, CrosswordSolvingMessage.SOLVING_ERROR_NO_CROSSWORD

    logger.info(f'Crossword successfully extracted in {round(time() - t1, 2)} sec.')

    return crossword, CrosswordSolvingMessage.SOLVED_SUCCESSFUL
