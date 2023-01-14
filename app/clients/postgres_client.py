from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.utils.docker_logs import get_logger
from app.utils.environments import Environments

logger = get_logger('postgres_client')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://' + Environments.POSTGRES_USER \
                                        + ':' + Environments.POSTGRES_PASSWORD \
                                        + '@' + Environments.POSTGRES_HOST \
                                        + ":" + Environments.POSTGRES_PORT \
                                        + '/' + Environments.POSTGRES_DB_NAME
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
