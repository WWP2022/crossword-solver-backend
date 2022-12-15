import json

from app.clients.postgres_client import db
from app.model.database.crossword_clue import CrosswordClue


def save_crossword_clue(crossword_clue: CrosswordClue):
    db.session.add(crossword_clue)
    db.session.commit()
    return crossword_clue


def find_crossword_clue_by_question_and_user_id(question: str, user_id: str):
    return db.session \
        .query(CrosswordClue) \
        .filter(CrosswordClue.question == question.upper()) \
        .filter(CrosswordClue.user_id == user_id) \
        .one_or_none()


def find_crossword_clues_by_user_id(user_id: str):
    return db.session \
        .query(CrosswordClue) \
        .filter(CrosswordClue.user_id == user_id) \
        .all()


def update_crossword_clue(crossword_clue: CrosswordClue, answers: str):
    crossword_clue.answers = answers
    db.session.commit()
    return crossword_clue


def add_answer_to_crossword_clue(crossword_clue, answer):
    answers = json.loads(crossword_clue.answers)
    answers += [answer]
    answers = list(set(answers))
    crossword_clue.answers = json.dumps(answers)
    db.session.commit()
    return crossword_clue


def delete_crossword_clue(crossword_clue: CrosswordClue):
    db.session.delete(crossword_clue)
    db.session.commit()
    return crossword_clue
