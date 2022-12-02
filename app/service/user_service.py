import shortuuid

from app.model.database.user import User
import app.repository.user_repository as rep


def register_new_user():
    user_id = shortuuid.uuid()
    while get_user_by_user_id(user_id) is not None:
        user_id = shortuuid.uuid()

    user = User(user_id=user_id)
    return rep.save_user(user)


def get_user_by_user_id(user_id):
    return rep.find_user_by_id(user_id)
