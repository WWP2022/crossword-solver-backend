import asyncio
import re


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

    def scrap_possible_answers_for_crossword(self):
        async def spawn_task():
            task_list = []

            for node in self.nodes:
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

    def solve(self):
        self.scrap_possible_answers_for_crossword()
        # TODO flaga czy coś przy iteracji się zmieniło
        # TODO Rozwiniecie algorytmu o backtracking
        for i in range(10):
            self.fill_crossword()
            self.remove_wrong_possible_answers()
