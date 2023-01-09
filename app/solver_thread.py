import threading

from app.clients.postgres_client import app
from app.service.crossword_service import solve_crossword_if_exist

POOL_TIME = 2

# lock to control access to variable
data_lock = threading.Lock()

# thread handler
solver_thread = threading.Thread()


def interrupt():
    global solver_thread
    solver_thread.cancel()


def solve_if_exist():
    global solver_thread
    with data_lock:
        with app.app_context():
            solve_crossword_if_exist()

    # create the new thread
    solver_thread = threading.Timer(POOL_TIME, solve_if_exist, ())
    solver_thread.start()


def solver_thread_start():
    global solver_thread
    # create first thread
    solver_thread = threading.Timer(POOL_TIME, solve_if_exist, ())
    solver_thread.start()
