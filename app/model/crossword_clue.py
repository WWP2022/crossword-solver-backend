import json

from app.clients.postgres_client import db


class CrosswordClue(db.Model):
    __tablename__ = "crossword_clue"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id = db.Column(db.String, unique=True, nullable=False)
    question = db.Column(db.String, unique=True, nullable=False)
    answers = db.Column(db.JSON, nullable=False)

    def __init__(self, user_id, question, answers):
        self.user_id = user_id
        self.question = question,
        self.answers = answers

    @property
    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question': self.question,
            'answers': self.answers
        }
