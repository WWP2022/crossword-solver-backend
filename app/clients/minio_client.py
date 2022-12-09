from minio import Minio

from app.model.database.crossword_info import CrosswordInfo
from app.utils.docker_logs import get_logger
from app.utils.variables import Variables

logger = get_logger('minio_client')

minio_client = Minio(
    Variables.MINIO_HOST + ":" + Variables.MINIO_PORT,
    access_key=Variables.MINIO_ACCESS_KEY,
    secret_key=Variables.MINIO_SECRET_KEY,
    secure=Variables.MINIO_SECURE
)

if not minio_client.bucket_exists(Variables.MINIO_BUCKET_NAME):
    minio_client.make_bucket(Variables.MINIO_BUCKET_NAME)


def put_processed_image(local_path: str, user_id: str, crossword_id: int):
    crossword_minio_path = user_id + "/" + str(crossword_id) + ".jpg"
    minio_client.fput_object(Variables.MINIO_BUCKET_NAME, crossword_minio_path, local_path)
    logger.info(f'Saved processed image with crossword_id: {crossword_id} for user_id: {user_id}')
    return crossword_minio_path


def put_unprocessed_image(unprocessed_image_path: str, user_id: str, crossword_id: int):
    crossword_minio_path = user_id + "/" + str(crossword_id) + "_unprocessed.jpg"
    minio_client.fput_object(Variables.MINIO_BUCKET_NAME, crossword_minio_path, unprocessed_image_path)
    logger.info(f'Saved unprocessed image with crossword_id: {crossword_id} for user_id: {user_id}')
    return crossword_minio_path


def get_processed_image(user_id: str, crossword_id: int):
    local_path = f'/tmp/{user_id}/{crossword_id}/processed_image.jpg'
    object_name = f'{user_id}/{crossword_id}.jpg'
    minio_client.fget_object(Variables.MINIO_BUCKET_NAME, object_name, local_path)
    logger.info(f'Got processed image: {crossword_id} for client: {user_id}')
    return local_path


def delete_processed_image(crossword_info: CrosswordInfo):
    minio_client.remove_object(Variables.MINIO_BUCKET_NAME, crossword_info.minio_path)
    logger.info(f'Deleted processed image: {crossword_info.id} for client: {crossword_info.user_id}')
