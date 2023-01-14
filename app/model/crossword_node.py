from enum import Enum

from app.scrapper.answer_scrapper import scrap_possible_solutions
from app.scrapper.definition_scrapper import scrap_most_similar_definition
from app.scrapper.final_answers_scrapper import scrap_lasts_solutions_for_incomplete_crossword


class GridPosition:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class AnswerDirection(Enum):
    RIGHT = 'right'
    DOWN = 'down'


class CrosswordNode:
    def __init__(self, ocr_definition, position_of_definition, direction, answer_start_position, length):
        self.ocr_definition = ocr_definition
        self.position_of_definition = position_of_definition
        self.direction = direction
        self.answer_start_position = answer_start_position
        self.length = length
        self.final_answer = ""
        self.possible_solutions = []
        self.possible_answers = []
        self.most_similar_definition = ""

    async def find_possible_answers(self):
        self.possible_solutions = await scrap_possible_solutions(self.ocr_definition, self.length)
        self.possible_answers = list(self.possible_solutions.keys())

    async def find_lasts_solutions_for_incomplete_crossword(self):
        self.possible_solutions = await scrap_lasts_solutions_for_incomplete_crossword(self.ocr_definition,
                                                                                       self.final_answer)
        self.possible_answers = list(self.possible_solutions.keys()) + list(self.possible_solutions.keys())

    async def get_most_similar_definition(self):
        self.most_similar_definition = await scrap_most_similar_definition(self.ocr_definition, self.final_answer)
