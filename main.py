from app.clients.postgres_client import app
from app.resource import another_resource
from app.resource import crossword_clue_resource

app.add_url_rule('/api/health', view_func=another_resource.hello)
app.add_url_rule('/api/solve', view_func=another_resource.solve)
app.add_url_rule('/api/register', view_func=another_resource.register)
app.add_url_rule('/api/login', view_func=another_resource.login)

app.add_url_rule('/api/crossword-clue', view_func=crossword_clue_resource.delete_crossword_clue)
app.add_url_rule('/api/crossword-clue', view_func=crossword_clue_resource.get_all_crossword_clues)
app.add_url_rule('/api/crossword-clue', view_func=crossword_clue_resource.add_crossword_clue)

if __name__ == "__main__":
    # start flask app
    app.run(host="0.0.0.0", port=5326)
