import aiohttp
from bs4 import BeautifulSoup

from app.model.solution_with_similarity import SolutionWithSimilarity
from app.utils.common import similar


async def scrap_most_similar_definition(ocr, final_answer):
    async with aiohttp.ClientSession() as session:
        data = {'wzorzec': final_answer}
        async with session.post("http://krzyzowkowo.pl/wyszukiwarka", data=data) as response:
            body = await response.text(errors="ignore")
            soup = BeautifulSoup(body, "html.parser")

            possible_solution_similarities = []

            for li_element in soup.find(name="div", attrs={"class": "content"}).find_all(name="li"):
                definition = li_element.getText().upper()

                possible_solution_similarities.append(
                    SolutionWithSimilarity(definition, final_answer, similar(definition, ocr)))

            possible_solution_similarities.sort(key=lambda element: element.similarity_of_definition, reverse=True)

            return possible_solution_similarities[0].definition if len(possible_solution_similarities) > 0 else ""
