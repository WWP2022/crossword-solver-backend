import os


class Environments:
    POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
    POSTGRES_DB_NAME = os.environ.get("POSTGRES_DB", "crossword-solver_dev")

    MINIO_HOST = os.environ.get("MINIO_HOST", "localhost")
    MINIO_PORT = os.environ.get("MINIO_PORT", "9000")
    MINIO_ACCESS_KEY = os.environ.get("MINIO_ROOT_USER", "admin")
    MINIO_SECRET_KEY = os.environ.get("MINIO_ROOT_PASSWORD", "admin123")
    MINIO_SECURE = False

    MINIO_BUCKET_NAME = "processed-images"
