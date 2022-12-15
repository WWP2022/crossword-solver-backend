import aiohttp
from bs4 import BeautifulSoup


async def find_possible_answers_1(search_meaning, search_crossword):
    async with aiohttp.ClientSession() as session:
        data = {'searchMeaning': search_meaning, 'searchCrossword': search_crossword}
        async with session.post("https://krzyzowki123.pl/searchForm", data=data) as response:
            body = await response.text()
            soup = BeautifulSoup(body, "html.parser")

            possible_answers = list(
                set(possible_answer.getText().upper() for possible_answer in
                    soup.findAll(name="td", attrs={"class": "pre"})))

            return possible_answers


async def find_possible_answers_2(search_meaning, length):
    async with aiohttp.ClientSession() as session:
        params = {'search': search_meaning, 'letters': length}
        async with session.get("https://szarada.net/slownik/wyszukiwarka-okreslen/", params=params) as response:
            body = await response.text()
            soup = BeautifulSoup(body, "html.parser")

            possible_answers = []
            for check in soup.findAll(name="td", attrs={"class": "checks"}):
                possible_answer = ''.join([item.text for item in check.findAll("span")])
                if len(possible_answer) == length:
                    possible_answers.append(possible_answer)

            possible_answers = possible_answers + [possible_answer.getText().upper() for possible_answer in
                                                   soup.findAll(name="span", attrs={"class": "answer"})]

            return possible_answers


async def find_possible_answers_3(search_meaning, length):
    async with aiohttp.ClientSession() as session:
        data = {'do': 'crossword', 'desc': search_meaning, 'letters': length}
        async with session.post("https://hasladokrzyzowek.com/krzyzowka/" + '-' * 6 + "/", data=data) as response:
            body = await response.text()
            soup = BeautifulSoup(body, "html.parser")

            possible_answers = list(
                set(possible_answer.getText().upper() for possible_answer in
                    soup.findAll(name="td", attrs={"class": "puzzal-name"})))

            return possible_answers


async def find_possible_answers(search_meaning, length):
    possible_answers_1 = await find_possible_answers_1(search_meaning, length)
    possible_answers_2 = await find_possible_answers_2(search_meaning, length)
    possible_answers_3 = await find_possible_answers_3(search_meaning, length)

    possible_answers = list(set(possible_answers_1 + possible_answers_2 + possible_answers_3))
    # TODO helpful print showing definition and found possible answers from remote servers
    print("Definition: " + str(search_meaning) + " length: " + str(length) + " possible answers: " + str(
        possible_answers))
    return possible_answers
