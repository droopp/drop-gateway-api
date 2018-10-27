
import sys
import os

from logging import DEBUG, Formatter, StreamHandler
from gevent import monkey
from flask import Flask

from flask_jwt import JWT
from werkzeug.security import safe_str_cmp
from datetime import timedelta


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id


users = [
    User(1, 'admin', 'admin123'),
]

DB_NAME = os.environ["DB_NAME"]
FLOWS_DIR = os.environ["FLOWS_DIR"]
DROP_HOME = os.environ["DROP_HOME"]
DROP_REPO = os.environ["DROP_REPO"]

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


monkey.patch_all()

app = Flask(__name__)
app.debug = False
app.config['SECRET_KEY'] = 'super-secret'
app.config['JWT_EXPIRATION_DELTA'] = timedelta(600)

jwt = JWT(app, authenticate, identity)

handler = StreamHandler(sys.stdout)
handler.setLevel(DEBUG)
handler.setFormatter(Formatter(
    '{"asctime":"%(asctime)s",\
    "level": "%(levelname)s",\
    "funcname": "%(funcName)s",\
    "message": "%(message)s"}'
))

app.logger.addHandler(handler)
app.logger.setLevel(DEBUG)


# modules

from app import drop_core
