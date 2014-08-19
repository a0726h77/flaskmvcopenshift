# -*- coding: utf-8 -*-
__version__ = '0.1'
from flask import Flask
app = Flask('project')
app.debug = True

# import controllers
from project.controllers import *

# import model
from models.models import db


#### initial logger ####
import logging
from logging.handlers import RotatingFileHandler
import os

LOG_PATH = '/'.join((os.path.dirname(os.path.realpath(__file__)), 'log'))
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)

handler = RotatingFileHandler(LOG_PATH + '/debug.log', maxBytes=10000, backupCount=1)
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
#### initial logger ####


#### initial sesion ####
from datetime import timedelta
app.config['SECRET_KEY'] = 'random'
app.permanent_session_lifetime = timedelta(seconds=60*60*10)  # session expire time
#### initial sesion ####


#### initial database ####
app.config.from_pyfile('config/database.cfg')
db.init_app(app)
with app.app_context():
    # db.drop_all()
    db.create_all()
#### initial database ####


#### router ####
from werkzeug.routing import Rule

urlpatterns = {
    Rule('/', endpoint='timeline'),
    Rule('/public', endpoint='public_timeline'),
    Rule('/<username>', endpoint='user_timeline'),
    Rule('/<username>/follow', endpoint='follow_user'),
    Rule('/<username>/unfollow', endpoint='unfollow_user'),
    Rule('/add_message', endpoint='add_message', methods=['POST']),
    Rule('/login', endpoint='login', methods=['GET', 'POST']),
    Rule('/register', endpoint='register', methods=['GET', 'POST']),
    Rule('/logout', endpoint='logout'),
}

for rule in urlpatterns:
    app.url_map.add(rule)
#### router ####
