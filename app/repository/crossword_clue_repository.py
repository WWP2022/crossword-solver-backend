from app.clients.postgres_client import db
from app.model.database.crossword_clue import CrosswordClue


def get_crossword_clue_by_question_and_user_id(question: str, user_id: str):
    return db.session \
        .query(CrosswordClue) \
        .filter(CrosswordClue.question == question) \
        .filter(CrosswordClue.user_id == user_id) \
        .one_or_none()


def get_crossword_clues_by_user_id(user_id: str):
    return db.session \
        .query(CrosswordClue) \
        .filter(CrosswordClue.user_id == user_id) \
        .all()


def save_crossword_clue(question: str, answers, user_id: str):
    crossword_clue = get_crossword_clue_by_question_and_user_id(question, user_id)
    if crossword_clue is not None:
        crossword_clue.answers = answers
        db.session.commit()
        return crossword_clue.serialize, 200

    crossword_clue_to_add = CrosswordClue(
        user_id=user_id,
        question=question,
        answers=answers
    )
    db.session.add(crossword_clue_to_add)
    db.session.commit()
    return crossword_clue_to_add


def delete_crossword_clue_by_question_and_user_id(question: str, user_id: str):
    crossword_clue = get_crossword_clue_by_question_and_user_id(question, user_id)
    if crossword_clue is None:
        return None

    db.session.delete(crossword_clue)
    db.session.commit()
    return crossword_clue
