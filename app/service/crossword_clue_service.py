import json

import app.repository.crossword_clue_repository as rep
from app.model.database.crossword_clue import CrosswordClue
from app.model.database.crossword_info import CrosswordInfo


def add_crossword_clue(question: str, answers: list[str], user_id: str):
    answers = list(set([answer.upper() for answer in answers]))
    crossword_clue_to_add = CrosswordClue(
        user_id=user_id,
        question=question.upper(),
        answers=json.dumps(answers)
    )
    return rep.save_crossword_clue(crossword_clue_to_add)


def add_questions_and_answers_from_crossword(crossword_info: CrosswordInfo):
    for node in json.loads(crossword_info.questions_and_answers):
        crossword_clue = rep.find_crossword_clue_by_question_and_user_id(node['question'], crossword_info.user_id)
        answer = node['answer']
        if crossword_clue is None:
            crossword_clue = CrosswordClue(
                user_id=crossword_info.user_id,
                question=node['question'].upper(),
                answers=json.dumps([answer])
            )
            rep.save_crossword_clue(crossword_clue)
            continue
        answers = json.loads(crossword_clue.answers)
        if answer not in answers:
            rep.add_answer_to_crossword_clue(crossword_clue, answer)


def update_crossword_clue(crossword_clue: CrosswordClue, answers: list[str]):
    answers = [answer.upper() for answer in answers]
    return rep.update_crossword_clue(crossword_clue, json.dumps(list(set(answers))))


def get_crossword_clue_by_question_and_user_id(question: str, user_id: str):
    return rep.find_crossword_clue_by_question_and_user_id(question.upper(), user_id)


def find_crossword_clues_by_user_id(user_id: str):
    return rep.find_crossword_clues_by_user_id(user_id)


def delete_crossword_clue_by_question_and_user_id(question: str, user_id: str):
    crossword_clue = rep.find_crossword_clue_by_question_and_user_id(question, user_id)
    if crossword_clue is None:
        return None
    return rep.delete_crossword_clue(crossword_clue)
