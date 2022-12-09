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

from app.hardcoded import hardcoded_crossword
from app.model.crossword_node import CrosswordNode
from app.model.database.crossword_info import CrosswordSolvingMessage
from app.model.ml.pytorchModel import Net
from app.utils.docker_logs import get_logger

logger = get_logger('extract_crossword')

filterwarnings('ignore')

CAT_MAPPING = {0: 'both', 1: 'double_text', 2: 'down', 3: 'inverse_arrow', 4: 'other', 5: 'right', 6: 'single_text'}

SOLVING_ERROR = None


def calc_coordinates(line):
    rho, theta = line.reshape(-1)
    a = np.cos(theta)
    b = np.sin(theta)
    x0 = a * rho
    y0 = b * rho
    x1 = int(x0 + 100000 * (-b))
    y1 = int(y0 + 100000 * (a))
    x2 = int(x0 - 100000 * (-b))
    y2 = int(y0 - 100000 * (a))

    return x1, y1, x2, y2


def calc_tangent(x1, y1, x2, y2):
    if (y2 - y1) != 0:
        return abs((x2 - x1) / (y2 - y1))
    else:
        return 1000


def get_lines(image, filter=True):
    '''
    The method finds each sudoku cell with Lines
    '''

    # apply some preprocessing before applying Hough transform
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 90, 150, apertureSize=3)
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    kernel = np.ones((5, 5), np.uint8)
    edges = cv2.erode(edges, kernel, iterations=1)

    # find lines on the preprocessed image u|sing Hough Transform
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 150)

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
            cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
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
    '''
    Adds some lines in case missing from standard methods
    '''

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
    for i, x in enumerate(xs[:-1]):
        for j, y in enumerate(ys[:-1]):
            cropImage = image[y:ys[j + 1], x:xs[i + 1]]
            cv2.imwrite(base_image_path + f'{j}_{i}.png', cropImage)


def ocr_core(filename):
    """
    This function will handle the core OCR processing of images.
    """

    image = cv2.imread(filename)
    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    text = pytesseract.image_to_string(image, lang='pol',
                                       config=r'--psm 1')  # We'll use Pillow's Image class to open the image and pytesseract to detect the string in the image
    return text


def find_arrows(data, i, j):
    '''
    Finds arrows adjacent to the current text displacement
    '''
    arrows = []
    try:
        arrow1 = data.iloc[i + 1, j]
    except:
        arrow1 = 'other'

    # if arrow is under the text fieled
    if arrow1 != 'double_text' and arrow1 != 'single_text' and arrow1 != 'other':
        if arrow1 == 'inverse_arrow':
            arrow1 = 'right'
            arrows.append([arrow1, i + 1, j])
        elif arrow1 == 'down':
            arrow1 = 'down'
            arrows.append([arrow1, i + 1, j])

    try:
        arrow2 = data.iloc[i, j + 1]
    except:
        arrow2 = 'other'

    # if arrow is to the right of the text field
    if arrow2 != 'double_text' and arrow2 != 'single_text' and arrow2 != 'other':
        if arrow2 == 'inverse_arrow':
            arrow2 = 'down'
            arrows.append([arrow2, i, j + 1])
        elif arrow2 == 'right':
            arrow2 = 'right'
            arrows.append([arrow2, i, j + 1])

    return arrows


def find_length(data, arrow):
    direction = arrow[0]
    start_row = arrow[1]
    start_col = arrow[2]
    counter = 1

    if direction == "down":
        while (len(data) > start_row + counter) and (data.iloc[start_row + counter, start_col] not in ["single_text",
                                                                                                       "double_text"]):
            counter += 1
        return counter

    else:
        while (11 > start_col + counter) and (data.iloc[start_row, start_col + counter] not in ["single_text",
                                                                                                "double_text"]):
            counter += 1
        return counter


def extract_crossword_to_model(data, base_image_path):
    crossword_nodes = []
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            # TODO after training model, we need to improve all functions called below
            if data.iloc[i, j] == 'single_text' or data.iloc[i, j] == 'double_text':
                arrows = find_arrows(data, i, j)
                text = ocr_core(base_image_path + f'{i}_{j}.png')
                for index, arrow in enumerate(arrows):
                    length = find_length(data, arrow)
                    crossword_nodes.append(
                        CrosswordNode(
                            definition=str(text),
                            position_of_definition=[i, j],
                            direction=arrow[0],
                            solution_start_position=[arrow[1], arrow[2]],
                            length=length
                        )
                    )
    # TODO create and return proper Crossword object
    crossword = hardcoded_crossword
    return crossword


def image_to_json(base_image_path, IMG_SHAPE=(64, 64), CAT_MAPPING={}):
    MODEL_PATH = str(Path(os.path.realpath(__file__)).parent) + "/model.pt"
    MATRIX_SIZE = sorted(list(map(lambda x: list(map(int, x.split('.')[0].split('_'))),
                                  [f for f in os.listdir(base_image_path) if "_" in f])))[-1]
    N_CLASSES = len(CAT_MAPPING)
    propertyMatrix = np.zeros((MATRIX_SIZE[0] + 1, MATRIX_SIZE[1] + 1))
    textualPropertyMatrix = pd.DataFrame(np.zeros((MATRIX_SIZE[0] + 1, MATRIX_SIZE[1] + 1)))

    # load model
    net = Net(N_CLASSES)
    net.load_state_dict(torch.load(MODEL_PATH))
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
        propertyMatrix[idxs[0], idxs[1]] = np.argmax(pred)
        textualPropertyMatrix.iloc[idxs[0], idxs[1]] = CAT_MAPPING[np.argmax(pred)]

    return extract_crossword_to_model(textualPropertyMatrix, base_image_path)


def extract_crossword(unprocessed_image_path, base_image_path):
    t1 = time()

    image = cv2.imread(unprocessed_image_path)

    # find crossword lines
    # print('Extracting grid from the crossword...\n')
    lines = get_lines(image, filter=True)

    if lines is None:
        logger.info(f'Error during processing: {CrosswordSolvingMessage.SOLVING_ERROR_NO_LINES.value}')
        return None, CrosswordSolvingMessage.SOLVING_ERROR_NO_LINES

    # corrects some missing lines
    lines = correct_lines(lines)

    # find line intersection points
    intersections = segmented_intersections(lines)

    # print('Creating crop for each crossword cell...\n')
    # crop each cell to a separate file
    create_crops(intersections, image, base_image_path)

    # print('Extracting JSON from the crossword...\n')
    # extract json from a given image
    crossword = image_to_json(base_image_path, CAT_MAPPING=CAT_MAPPING)

    logger.info(f'Crossword successfully solved in {time() - t1} seconds')

    return crossword, CrosswordSolvingMessage.SOLVED_SUCCESSFUL
