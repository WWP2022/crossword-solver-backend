from sqlalchemy import func, DECIMAL, cast

from app.clients.postgres_client import db
from app.model.database.crossword_info import CrosswordInfo


def save_crossword_info(crossword_info: CrosswordInfo):
    db.session.add(crossword_info)
    db.session.commit()
    return crossword_info


def update_crossword_info_status_and_minio_path(
        crossword_info: CrosswordInfo,
        status: str,
        minio_path: str,
        questions_and_answers: str):
    crossword_info.status = status
    crossword_info.minio_path = minio_path
    crossword_info.questions_and_answers = questions_and_answers
    db.session.commit()
    return crossword_info


def update_crossword_info_status_by_crossword_info_id(crossword_info_id: str, status: str):
    crossword_info = db.session \
        .query(CrosswordInfo) \
        .filter(CrosswordInfo.id == crossword_info_id) \
        .one_or_none()
    crossword_info.status = status
    db.session.commit()
    return crossword_info


def update_crossword(crossword_info: CrosswordInfo, crossword_name: str, status: str):
    crossword_info.status = status
    crossword_info.crossword_name = crossword_name if crossword_name is not None else crossword_info.crossword_name
    db.session.commit()
    return crossword_info


def find_crosswords_info_by_user_id(user_id: str):
    return db.session \
        .query(CrosswordInfo) \
        .filter(CrosswordInfo.user_id == user_id) \
        .all()


def find_crossword_info_by_crossword_id(crossword_id: int):
    return db.session \
        .query(CrosswordInfo) \
        .filter(CrosswordInfo.id == crossword_id) \
        .one_or_none()


def delete_crossword_info(crossword_info: CrosswordInfo):
    db.session.delete(crossword_info)
    db.session.commit()
    return crossword_info


def find_last_default_name_by_user_id(user_d: str):
    return db.session \
        .query(CrosswordInfo) \
        .filter(CrosswordInfo.user_id == user_d) \
        .filter(CrosswordInfo.crossword_name.regexp_match('Krzyżówka-\d+$')) \
        .order_by(cast(func.regexp_replace(CrosswordInfo.crossword_name, "\\D", "", "g"), DECIMAL).desc()) \
        .first()


def find_crossword_info_by_crossword_name_and_user_id(crossword_name: str, user_id: str):
    return db.session \
        .query(CrosswordInfo) \
        .filter(CrosswordInfo.user_id == user_id) \
        .filter(CrosswordInfo.crossword_name == crossword_name) \
        .one_or_none()
