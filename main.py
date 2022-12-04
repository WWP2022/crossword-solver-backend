import atexit

from app.clients.postgres_client import app
from app.resource import crossword_clue_resource, solver_resource, \
    health_resource, user_resource, crossword_resource
from app.solver_thread import interrupt, solver_thread_start

app.add_url_rule('/api/crossword-clue', view_func=crossword_clue_resource.delete_crossword_clue)
app.add_url_rule('/api/crossword-clue', view_func=crossword_clue_resource.get_all_crossword_clues)
app.add_url_rule('/api/crossword-clue', view_func=crossword_clue_resource.add_crossword_clue)

app.add_url_rule('/api/crossword/status', view_func=crossword_resource.status)
app.add_url_rule('/api/crossword', view_func=crossword_resource.get_solved_crossword)
app.add_url_rule('/api/crossword', view_func=crossword_resource.update_crossword)
app.add_url_rule('/api/crossword', view_func=crossword_resource.delete_crossword)
app.add_url_rule('/api/crossword/all', view_func=crossword_resource.get_solved_crossword_ids_names_and_timestamps)

app.add_url_rule('/api/health', view_func=health_resource.hello)

app.add_url_rule('/api/solver', view_func=solver_resource.solve)

app.add_url_rule('/api/register', view_func=user_resource.register)
app.add_url_rule('/api/login', view_func=user_resource.login)

if __name__ == "__main__":
    # start thread for solving crosswords
    solver_thread_start()
    # after killing flask also clear trigger for next thread
    atexit.register(interrupt)
    # start flask app
    app.run(host="0.0.0.0", port=5326)
