import os


class Variables:
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    DATABASE = os.environ.get("POSTGRES_DB", "crossword-solver_dev")
    DATABASE_PORT = os.environ.get("POSTGRES_PORT", "5432")
    USER = os.environ.get("POSTGRES_USER", "postgres")
    PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")

    MINIO_HOST = os.environ.get("MINIO_HOST", "localhost")
    MINIO_PORT = os.environ.get("MINIO_PORT", "9000")

    ACCESS_KEY = os.environ.get("MINIO_ROOT_USER", "admin")
    SECRET_KEY = os.environ.get("MINIO_ROOT_PASSWORD", "admin123")
    SECURE = False

    BUCKET_NAME = "processed-images"
