from app.processing.answer_scrapper import find_possible_answers


class CrosswordNode:
    def __init__(self, definition, position_of_definition, direction, solution_start_position, length):
        self.definition = definition
        self.position_of_definition = position_of_definition
        self.direction = direction
        self.solution_start_position = solution_start_position
        self.length = length
        self.solution = ""
        self.possible_answers = []

    async def scrap_possible_answers(self):
        self.possible_answers = await find_possible_answers(self.definition, self.length)
