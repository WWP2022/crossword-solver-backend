import asyncio
import copy
import json
import re
from time import time

from app.model.database.crossword_clue import CrosswordClue
from app.service import crossword_clue_service
from app.utils.docker_logs import get_logger

logger = get_logger('crossword_solver')


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

    def is_crossword_solved(self):
        number_of_dots = 0
        for line in self.data:
            number_of_dots += line.count(".")
        return number_of_dots == 0

    def get_node_solution_from_data(self, node):
        solution = ""
        if node.direction == "right":
            solution = self.data[node.solution_start_position[0]][
                       node.solution_start_position[1]:node.solution_start_position[1] + node.length]
        else:
            for i in range(node.length):
                solution = solution + self.data[node.solution_start_position[0] + i][node.solution_start_position[1]]
        return solution

    def extract_solutions_to_nodes_from_data(self):
        for node in self.nodes:
            if node.solution == "":
                solution = self.get_node_solution_from_data(node)
                if solution.count(".") == 0:
                    node.solution = solution
        self.nodes = list(filter(lambda element: element.solution != "", self.nodes))

    def is_better_than(self, other_crossword):
        solved_places = 0
        for line in self.data:
            solved_places += len(line.replace(".", "").replace("#", ""))

        solved_places_for_other_solution = 0
        for line in other_crossword.data:
            solved_places_for_other_solution += len(line.replace(".", "").replace("#", ""))

        return solved_places > solved_places_for_other_solution

    def scrap_possible_answers_for_crossword(self, user_id: str):
        async def spawn_task():
            task_list = []

            for node in self.nodes:
                # TODO consider to remove this line
                # correct_question = spell_corrector.correct_question(node.definition)
                correct_question = node.definition
                crossword_clue: CrosswordClue = crossword_clue_service.get_crossword_clue_by_question_and_user_id(
                    correct_question,
                    user_id
                )
                if crossword_clue is not None:
                    node.possible_answers = json.loads(crossword_clue.answers)
                else:
                    task_list.append(asyncio.create_task(node.scrap_possible_answers()))

            await asyncio.gather(*task_list)

        asyncio.run(spawn_task())

    def fill_crossword_and_remove_wrong_possible_answers(self):
        is_something_changed = False
        for node in self.nodes:
            if len(node.possible_answers) == 1 and node.solution == "":
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
                is_something_changed = True

        for node in self.nodes:
            regex = re.compile(self.get_node_solution_from_data(node))
            filtered = [i for i in node.possible_answers if regex.match(i)]
            node.possible_answers = filtered
        return is_something_changed

    def solve(self, user_id: str):
        start_solving_time = time()
        self.scrap_possible_answers_for_crossword(user_id)
        crossword = self._solve_crossword()
        self.nodes = crossword.nodes
        self.data = crossword.data
        self.extract_solutions_to_nodes_from_data()
        logger.info(f'Solving time: {round(time() - start_solving_time, 2)} sec.')

    def print_result(self):
        for result in self.data:
            print(result)

    def _solve_crossword(self):
        while self.fill_crossword_and_remove_wrong_possible_answers():
            pass

        if self.is_crossword_solved():
            return self

        best_crossword = copy.deepcopy(self)

        self.nodes.sort(key=lambda element: len(element.possible_answers), reverse=False)
        for node in self.nodes:
            if len(node.possible_answers) > 1:
                tmp_possible_answers = node.possible_answers
                for possible_answer in tmp_possible_answers:
                    node.possible_answers = [possible_answer]
                    crossword_copy = copy.deepcopy(self)
                    tmp_crossword = crossword_copy._solve_crossword()
                    if tmp_crossword.is_better_than(best_crossword):
                        best_crossword = copy.deepcopy(tmp_crossword)
                    node.solution = ""
                node.possible_answers = tmp_possible_answers
                break
        return best_crossword
