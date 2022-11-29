from minio import Minio

from app.utils.docker_logs import get_logger
from app.utils.variables import Variables

logger = get_logger('minio_client')

minio_client = Minio(
    Variables.MINIO_HOST + ":" + Variables.MINIO_PORT,
    access_key=Variables.ACCESS_KEY,
    secret_key=Variables.SECRET_KEY,
    secure=Variables.SECURE
)

if not minio_client.bucket_exists(Variables.BUCKET_NAME):
    minio_client.make_bucket(Variables.BUCKET_NAME)


def put_processed_image(user_id, file):
    file_name = file.rsplit('/', 1)[-1]  # get only crossword_name
    path = user_id + "/" + file_name
    minio_client.fput_object(Variables.BUCKET_NAME, path, file)
    logger.info(f'save processed image for client: {user_id}')
