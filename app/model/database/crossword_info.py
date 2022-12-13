from enum import Enum

from app.clients.postgres_client import db, app


class CrosswordStatus(Enum):
    NEW = 'new'
    CANNOT_SOLVE = 'cannot_solve'
    SOLVING = 'solving'
    SOLVED_WAITING = 'solved_waiting'
    SOLVED_ACCEPTED = 'solved_accepted'


class CrosswordSolvingMessage(Enum):
    SOLVED_SUCCESSFUL = 'solved_successfully'
    SOLVING_ERROR_NO_LINES = 'lines_not_found'
    SOLVING_ERROR_NO_CROSSWORD = "crossword_not_found"
    SOLVING_ERROR_CANNOT_CROPPED_IMAGES = "cannot_cropped_images"


class CrosswordInfo(db.Model):
    __tablename__ = "crossword_info"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String, nullable=False)
    crossword_name = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False, default=CrosswordStatus.NEW.value)
    minio_path = db.Column(db.String, unique=True)
    questions_and_answers = db.Column(db.JSON)
    solving_message = db.Column(db.String)
    timestamp = db.Column(db.String, nullable=False)

    def __init__(self, user_id, crossword_name, timestamp):
        self.user_id = user_id
        self.crossword_name = crossword_name,
        self.timestamp = timestamp

    @property
    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'crossword_name': self.question,
            'status': self.status,
            'minio_path': self.minio_path,
            'questions_and_answers': self.questions_and_answers,
            'solving_message': self.solving_message,
            'timestamp': self.timestamp
        }


with app.app_context():
    db.create_all()
