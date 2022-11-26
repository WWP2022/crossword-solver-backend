import os
from minio import Minio

from app.utils.docker_logs import get_logger

logger = get_logger('minio_client')


HOST = os.environ.get("MINIO_HOST", "localhost")
PORT = os.environ.get("MINIO_PORT", "9000")
HOST_WITH_PORT = HOST + ":" + PORT

ACCESS_KEY = os.environ.get("MINIO_ROOT_USER", "admin")
SECRET_KEY = os.environ.get("MINIO_ROOT_PASSWORD", "admin123")
SECURE = False

BUCKET_NAME = "processed-images"

minio_client = Minio(
    HOST_WITH_PORT,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    secure=SECURE
)

if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)


def put_processed_image(user_id, file):
    file_name = file.rsplit('/', 1)[-1]  # get only crossword_name
    path = user_id + "/" + file_name
    minio_client.fput_object(BUCKET_NAME, path, file)
    logger.info(f'save processed image for client: {user_id}')
