from app.clients.postgres_client import db, app


class CrosswordTask(db.Model):
    __tablename__ = "crossword_task"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    crossword_info_id = db.Column(db.Integer, db.ForeignKey('crossword_info.id'))
    unprocessed_image_path = db.Column(db.String, unique=True, nullable=False)
    base_image_path = db.Column(db.String, unique=True, nullable=False)
    user_id = db.Column(db.String, nullable=False)

    def __init__(self, crossword_info_id, unprocessed_image_path, base_image_path, user_id):
        self.crossword_info_id = crossword_info_id,
        self.unprocessed_image_path = unprocessed_image_path,
        self.base_image_path = base_image_path,
        self.user_id = user_id


with app.app_context():
    db.create_all()
