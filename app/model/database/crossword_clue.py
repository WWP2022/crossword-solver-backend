from app.clients.postgres_client import db, app


class CrosswordClue(db.Model):
    __tablename__ = "crossword_clue"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, nullable=False)
    question = db.Column(db.String, nullable=False)
    answers = db.Column(db.JSON, nullable=False)
    is_perfect = db.Column(db.Boolean, nullable=False)

    def __init__(self, user_id, question, answers, is_perfect):
        self.user_id = user_id
        self.question = question
        self.answers = answers
        self.is_perfect = is_perfect

    @property
    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question': self.question,
            'answers': self.answers
        }


with app.app_context():
    db.create_all()
