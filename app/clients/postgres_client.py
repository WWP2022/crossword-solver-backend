from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.utils.docker_logs import get_logger
from app.utils.variables import Variables

logger = get_logger('postgres_client')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://' + Variables.USER \
                                        + ':' + Variables.PASSWORD \
                                        + '@' + Variables.POSTGRES_HOST \
                                        + ":" + Variables.DATABASE_PORT \
                                        + '/' + Variables.DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
