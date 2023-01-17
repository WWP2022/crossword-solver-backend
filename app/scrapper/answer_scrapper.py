import aiohttp
from bs4 import BeautifulSoup


# TODO Rewrite this after train model on new crosswords
# async def scrap_from_krzyzowki123(search_meaning, search_crossword):
#     async with aiohttp.ClientSession() as session:
#         data = {'searchMeaning': search_meaning, 'searchCrossword': search_crossword}
#         async with session.post("https://krzyzowki123.pl/searchForm", data=data) as response:
#             body = await response.text(errors="ignore")
#             soup = BeautifulSoup(body, "html.parser")
#
#             possible_answers = list(
#                 set(possible_answer.getText().upper() for possible_answer in
#                     soup.findAll(name="td", attrs={"class": "pre"})))
#
#             return possible_answers


async def scrap_from_szarada(ocr_definition, length):
    async with aiohttp.ClientSession() as session:
        params = {'search': ocr_definition, 'letters': length}
        async with session.get("https://szarada.net/slownik/wyszukiwarka-okreslen/", params=params) as response:
            body = await response.text()
            soup = BeautifulSoup(body, "html.parser")

            possible_solutions = {}

            # First level of possible answers
            definition = soup.find(name="div", attrs={"id": "main-panel"}).find("h1").text.upper()
            for check in soup.findAll(name="td", attrs={"class": "checks"}):
                answer = ''.join([item.text for item in check.findAll("span")])
                if len(answer) == length:
                    possible_solutions[answer] = definition

            # Second level of possible answers
            if len(possible_solutions) == 0:
                for possible_solution in soup.findAll(name="span", attrs={"class": "answer"}):
                    answer = possible_solution.getText().upper()
                    if len(answer) == length and answer not in possible_solutions and len(possible_solutions) < 5:
                        possible_solutions[answer] = ocr_definition

            # Third level of possible answers
            if len(possible_solutions) == 0:
                for possible_solution in soup.findAll(name="td", attrs={"class": "answer"}):
                    answer = possible_solution.getText().upper()
                    definition = possible_solution.nextSibling.getText().upper()
                    if len(answer) == length and answer not in possible_solutions and len(possible_solutions) < 5:
                        possible_solutions[answer] = definition

            return possible_solutions


# TODO Rewrite this after train model on new crosswords
# async def scrap_from_hasladokrzyzowek(search_meaning, length):
#     async with aiohttp.ClientSession() as session:
#         data = {'do': 'crossword', 'desc': search_meaning, 'letters': length}
#         async with session.post("https://hasladokrzyzowek.com/krzyzowka/" + '-' * 6 + "/", data=data) as response:
#             body = await response.text()
#             soup = BeautifulSoup(body, "html.parser")
#
#             possible_answers = list(
#                 set(possible_answer.getText().upper() for possible_answer in
#                     soup.findAll(name="td", attrs={"class": "puzzal-name"})))
#
#             return possible_answers


async def scrap_possible_solutions(ocr_definition, length):
    # possible_answers_krzyzowki123 = await scrap_from_krzyzowki123(search_meaning, length)
    possible_solutions_szarada = await scrap_from_szarada(ocr_definition, length)
    # possible_answers_hasladokrzyzowek = await scrap_from_hasladokrzyzowek(search_meaning, length)

    # possible_answers = list(set(possible_answers_1 + possible_answers_2 + possible_answers_3))
    # possible_answers = list(set(possible_answers_2))
    # Set above change the order in list

    # TODO consider to cat elements if this list is too long
    possible_solutions = possible_solutions_szarada  # list(possible_solutions_szarada)[0:len(possible_solutions_szarada)]
    # TODO helpful print showing definition and found possible answers from remote servers
    print(ocr_definition + " " + str(length) + " " + str(possible_solutions))

    return possible_solutions
