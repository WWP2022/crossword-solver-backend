from app.clients.postgres_client import db
from app.model.database.crossword_task import CrosswordTask


def save_crossword_task(crossword_task: CrosswordTask):
    db.session.add(crossword_task)
    db.session.commit()
    return crossword_task


def find_crossword_task():
    return db.session \
        .query(CrosswordTask) \
        .first()


def delete_crossword_task(crossword_task: CrosswordTask):
    db.session.delete(crossword_task)
    db.session.commit()
    return crossword_task
