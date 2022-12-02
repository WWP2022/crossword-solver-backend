from app.clients.postgres_client import app


@app.route('/api/health', methods=['GET'])
def hello():
    return 'Hello world'
