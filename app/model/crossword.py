import asyncio
import re

from app.model.database.crossword_clue import CrosswordClue
from app.service import crossword_clue_service
from app.utils import spell_corrector


class Crossword:
    def __init__(self, row_number, col_number, nodes):
        self.row_number = row_number
        self.col_number = col_number
        self.nodes = nodes
        self.data = ["." * col_number for _ in range(row_number)]

        for node in nodes:
            line = self.data[node.position_of_definition[0]]
            line = line[:node.position_of_definition[1]] + "#" + line[node.position_of_definition[1] + 1:]
            self.data[node.position_of_definition[0]] = line

    def solve(self, user_id: str):
        self.scrap_possible_answers_for_crossword(user_id)
        # TODO flaga czy coś przy iteracji się zmieniło
        # TODO Rozwiniecie algorytmu o backtracking
        for i in range(10):
            self.fill_crossword()
            self.remove_wrong_possible_answers()

    def scrap_possible_answers_for_crossword(self, user_id: str):
        async def spawn_task():
            task_list = []

            for node in self.nodes:
                correct_question = spell_corrector.correct_question(node.definition)
                crossword_clue: CrosswordClue = crossword_clue_service.get_crossword_clue_by_question_and_user_id(
                    correct_question,
                    user_id
                )
                if crossword_clue is not None:
                    node.possible_answers = crossword_clue.answers
                else:
                    task_list.append(asyncio.create_task(node.scrap_possible_answers()))

            await asyncio.gather(*task_list)

        asyncio.run(spawn_task())

    def fill_crossword(self):
        for node in self.nodes:
            if len(node.possible_answers) == 1:
                node.solution = node.possible_answers[0]
                if node.direction == "down":
                    for idx, x in enumerate(node.possible_answers[0]):
                        line = self.data[node.solution_start_position[0] + idx]
                        line = line[:node.solution_start_position[1]] + x + line[node.solution_start_position[1] + 1:]
                        self.data[node.solution_start_position[0] + idx] = line
                else:
                    for idx, x in enumerate(node.possible_answers[0]):
                        line = self.data[node.solution_start_position[0]]
                        line = line[:node.solution_start_position[1] + idx] + x + line[node.solution_start_position[
                                                                                           1] + idx + 1:]
                        self.data[node.solution_start_position[0]] = line

    def remove_wrong_possible_answers(self):
        for node in self.nodes:
            regex = ""
            if node.direction == "right":
                regex = self.data[node.solution_start_position[0]][
                        node.solution_start_position[1]:node.solution_start_position[1] + node.length]
            else:
                for i in range(node.length):
                    regex = regex + self.data[node.solution_start_position[0] + i][node.solution_start_position[1]]

            regex = re.compile(regex)
            filtered = [i for i in node.possible_answers if regex.match(i)]
            node.possible_answers = filtered

    def print_result(self):
        for result in self.data:
            print(result)
