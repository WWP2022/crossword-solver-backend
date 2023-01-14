import asyncio
import copy
import re
from time import time

from app.model.crossword_node import AnswerDirection
from app.model.database.crossword_clue import CrosswordClue
from app.service import crossword_clue_service
from app.utils.docker_logs import get_logger

logger = get_logger('crossword_solver')


class Crossword:
    def __init__(self, row_number, col_number, nodes):
        self.row_number = row_number
        self.col_number = col_number
        self.nodes = nodes
        self.grid = ["." * col_number for _ in range(row_number)]

        # Fill grid with hash in place where definition field is
        for node in nodes:
            line = self.grid[node.position_of_definition.x]
            line = line[:node.position_of_definition.y] + "#" + line[node.position_of_definition.y + 1:]
            self.grid[node.position_of_definition.x] = line

    def is_crossword_solved(self):
        number_of_dots = 0
        for line in self.grid:
            number_of_dots += line.count(".")
        return number_of_dots == 0

    def get_final_answer_for_node(self, node):
        final_answer = ""
        if node.direction == AnswerDirection.RIGHT:
            final_answer = self.grid[node.answer_start_position.x][
                           node.answer_start_position.y:node.answer_start_position.y + node.length]
        else:
            for i in range(node.length):
                final_answer = final_answer + self.grid[node.answer_start_position.x + i][
                    node.answer_start_position.y]
        return final_answer

    def extract_final_answers_from_grid(self):
        for node in self.nodes:
            if node.final_answer == "":
                node.final_answer = self.get_final_answer_for_node(node)

    def is_better_solved_than(self, other_crossword):
        solved_fields = 0
        for line in self.grid:
            solved_fields += len(line.replace(".", "").replace("#", ""))

        solved_fields_for_other_solution = 0
        for line in other_crossword.grid:
            solved_fields_for_other_solution += len(line.replace(".", "").replace("#", ""))

        return solved_fields > solved_fields_for_other_solution

    def get_possible_answers_for_crossword(self, user_id: str):
        async def spawn_task():
            scrap_tasks = []

            for node in self.nodes:
                # TODO consider to remove this line
                # correct_question = spell_corrector.correct_question(node.ocr_definition)
                correct_question = node.ocr_definition
                crossword_clue: CrosswordClue = crossword_clue_service.get_crossword_clue_by_question_and_user_id(
                    correct_question,
                    user_id
                )
                if crossword_clue is not None:
                    node.possible_answers = crossword_clue.answers
                else:
                    scrap_tasks.append(asyncio.create_task(node.find_possible_answers()))

            await asyncio.gather(*scrap_tasks)

        asyncio.run(spawn_task())

    def fill_crossword_and_remove_wrong_possible_answers(self):
        is_something_changed = False
        for node in self.nodes:
            if len(node.possible_answers) == 1 and node.final_answer == "":
                node.final_answer = node.possible_answers[0]

                for idx, x in enumerate(node.final_answer):
                    if node.direction == AnswerDirection.RIGHT:
                        line = self.grid[node.answer_start_position.x]
                        line = line[:node.answer_start_position.y + idx] + x + line[
                                                                               node.answer_start_position.y + idx + 1:]
                        self.grid[node.answer_start_position.x] = line

                    else:
                        line = self.grid[node.answer_start_position.x + idx]
                        line = line[:node.answer_start_position.y] + x + line[node.answer_start_position.y + 1:]
                        self.grid[node.answer_start_position.x + idx] = line

                is_something_changed = True

        for node in self.nodes:
            regex = re.compile(self.get_final_answer_for_node(node))
            filtered = [i for i in node.possible_answers if regex.match(i)]
            node.possible_answers = filtered

        return is_something_changed

    def get_lasts_solutions_for_incomplete_crossword(self):
        async def spawn_task():
            scrap_tasks = []

            for node in self.nodes:
                if node.final_answer.count(".") != 0:
                    scrap_tasks.append(asyncio.create_task(node.find_lasts_solutions_for_incomplete_crossword()))

            await asyncio.gather(*scrap_tasks)

        asyncio.run(spawn_task())

    def solve(self, user_id: str):
        start_solving_time = time()

        self.get_possible_answers_for_crossword(user_id)
        crossword = self._solve_crossword()

        self.nodes = crossword.nodes
        self.grid = crossword.grid

        self.extract_final_answers_from_grid()

        # solve again because crossword gain new few solutions after first solving
        self.get_lasts_solutions_for_incomplete_crossword()
        crossword = self._solve_crossword()

        self.nodes = crossword.nodes
        self.grid = crossword.grid

        self.extract_final_answers_from_grid()

        # We want save in database only solved nodes, so we filter out unsolved ones
        self.nodes = list(filter(lambda element: element.final_answer.count(".") == 0, self.nodes))

        logger.info(f'Solving time: {round(time() - start_solving_time, 2)} sec.')

    def print_crossword(self):
        for result in self.grid:
            print(result)

    def extract_questions_with_answers(self):

        # scrapping most similar definition to ocr version for each node
        async def spawn_task():
            scrap_tasks = []

            for node in self.nodes:
                scrap_tasks.append(asyncio.create_task(node.get_most_similar_definition()))
            await asyncio.gather(*scrap_tasks)

        asyncio.run(spawn_task())

        # Solutions comes from ocr, where are some typos
        not_perfect_solutions = [{"question": node.ocr_definition,
                                  "answer": [node.final_answer],
                                  "is_perfect": False} for node in self.nodes if
                                 node.most_similar_definition != node.ocr_definition]

        # Solutions comes from perfect ocr or scrapped definition
        perfect_solutions = [{"question": node.most_similar_definition,
                              "answer": [node.final_answer],
                              "is_perfect": True} for node in self.nodes if node.most_similar_definition != ""]

        return not_perfect_solutions + perfect_solutions

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
                    if tmp_crossword.is_better_solved_than(best_crossword):
                        best_crossword = copy.deepcopy(tmp_crossword)
                    node.final_answer = ""
                node.possible_answers = tmp_possible_answers
                break
        return best_crossword
