import shortuuid

from app.model.database.user import User
from app.repository.user_repository import find_user_by_id, add_new_user


def register_new_user():
    user_id = shortuuid.uuid()
    while get_user_by_user_id(user_id) is not None:
        user_id = shortuuid.uuid()

    user = User(user_id=user_id)
    add_new_user(user)

    return user


def get_user_by_user_id(user_id):
    return find_user_by_id(user_id)
