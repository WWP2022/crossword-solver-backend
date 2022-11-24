import psycopg2

HOST = "localhost"
DATABASE = "crossword-solver_dev"
USER = "postgres"
PASSWORD = "postgres"

conn = psycopg2.connect(
        host=HOST,
        database=DATABASE,
        user=USER,
        password=PASSWORD)

cur = conn.cursor()
