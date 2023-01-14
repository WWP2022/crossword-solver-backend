import aiohttp
from bs4 import BeautifulSoup

from app.model.solution_with_similarity import SolutionWithSimilarity
from app.utils.common import similar


async def scrap_lasts_solutions_for_incomplete_crossword(search_meaning, letters):
    async with aiohttp.ClientSession() as session:
        letters = letters.replace(".", "-")
        async with session.get("https://krzyzowki123.pl/haslo/" + letters) as response:
            body = await response.text()
            soup = BeautifulSoup(body, "html.parser")

            possible_solutions = {}
            possible_solution_similarities = []

            for possible_solution in soup.findAll(name="td", attrs={"class": "col-33 bold ttu pre ow"}):
                answer = possible_solution.getText().upper()
                definition = possible_solution.nextSibling.getText()

                possible_solution_similarities.append(
                    SolutionWithSimilarity(definition, answer, similar(definition, search_meaning)))

            possible_solution_similarities.sort(key=lambda element: element.similarity_of_definition, reverse=True)
            possible_solution_similarities = possible_solution_similarities[0:1]

            for possible_solution_similarity in possible_solution_similarities:
                possible_solutions[possible_solution_similarity.answer] = possible_solution_similarity.definition

            # TODO useful print showing lasts solutions and you can check if some solution are written to crossword
            print(possible_solutions)

            return possible_solutions
