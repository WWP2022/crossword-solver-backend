import datetime

from app.clients.postgres_client import db, app


class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column(db.String, primary_key=True)
    created = db.Column(db.Date, nullable=False)
    sent_crosswords = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, user_id):
        self.user_id = user_id
        self.created = datetime.date.today()
        self.sent_crosswords = 0

    @property
    def serialize(self):
        return {
            'user_id': self.user_id,
            'created': str(self.created),
            'sent_crosswords': self.sent_crosswords
        }


with app.app_context():
    db.create_all()
