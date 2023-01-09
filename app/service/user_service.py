import shortuuid

import app.repository.user_repository as rep
from app.model.database.user import User


def register_new_user():
    user_id = shortuuid.uuid()
    while get_user_by_user_id(user_id) is not None:
        user_id = shortuuid.uuid()

    user = User(user_id=user_id)
    return rep.save_user(user)


def get_user_by_user_id(user_id):
    return rep.find_user_by_id(user_id)


def update_number_of_crosswords(user_id, sent_crosswords):
    return rep.update_number_of_crosswords(user_id, sent_crosswords)
