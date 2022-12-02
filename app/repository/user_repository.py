from app.clients.postgres_client import db
from app.model.database.user import User


def save_user(user: User):
    db.session.add(user)
    db.session.commit()
    return user


def find_user_by_id(user_id: str):
    return db.session \
        .query(User) \
        .filter(User.user_id == user_id) \
        .one_or_none()
