from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.utils.docker_logs import get_logger
from app.utils.variables import Variables

logger = get_logger('postgres_client')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://' + Variables.POSTGRES_USER \
                                        + ':' + Variables.POSTGRES_PASSWORD \
                                        + '@' + Variables.POSTGRES_HOST \
                                        + ":" + Variables.POSTGRES_PORT \
                                        + '/' + Variables.POSTGRES_DB_NAME
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
