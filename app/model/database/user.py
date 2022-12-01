from app.clients.postgres_client import db, app


class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column(db.String, primary_key=True)

    def __init__(self, user_id):
        self.user_id = user_id

    @property
    def serialize(self):
        return {
            'user_id': self.user_id
        }


with app.app_context():
    db.create_all()
