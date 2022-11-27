import os
import psycopg2

from app.utils.docker_logs import get_logger

logger = get_logger('postgres_client')

HOST = os.environ.get("POSTGRES_HOST", "localhost")
DATABASE = os.environ.get("POSTGRES_DB", "crossword-solver_dev")
USER = os.environ.get("POSTGRES_USER", "postgres")
PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")

conn = psycopg2.connect(
    host=HOST,
    database=DATABASE,
    user=USER,
    password=PASSWORD)

cursor = conn.cursor()
