import app.repository.crossword_clue_repository as rep
from app.model.database.crossword_clue import CrosswordClue


def add_crossword_clue(question: str, answers, user_id: str):
    crossword_clue_to_add = CrosswordClue(
        user_id=user_id,
        question=question,
        answers=answers
    )
    return rep.save_crossword_clue(crossword_clue_to_add)


def update_crossword_clue(crossword_clue: CrosswordClue, answers: str):
    return rep.update_crossword_clue(crossword_clue, answers)


def get_crossword_clue_by_question_and_user_id(question, user_id):
    return rep.find_crossword_clue_by_question_and_user_id(question, user_id)


def delete_crossword_clue_by_question_and_user_id(question: str, user_id: str):
    crossword_clue = rep.find_crossword_clue_by_question_and_user_id(question, user_id)
    if crossword_clue is None:
        return None
    return rep.delete_crossword_clue(crossword_clue)
