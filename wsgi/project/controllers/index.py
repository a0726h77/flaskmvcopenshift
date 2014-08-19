# -*- coding: utf-8 -*-
"""
    MiniTwit
    ~~~~~~~~

    A microblogging application written with Flask and sqlite3.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from project import app
import time
from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack
from werkzeug import check_password_hash, generate_password_hash

from project.models.models import db
from project.models.user import User

# configuration
# PER_PAGE = 30

# create our little application :)
# app = Flask(__name__)
# app.config.from_object(__name__)
# app.config.from_envvar('MINITWIT_SETTINGS', silent=True)


# def get_db():
#     """Opens a new database connection if there is none yet for the
#     current application context.
#     """
#     top = _app_ctx_stack.top
#     if not hasattr(top, 'sqlite_db'):
#         top.sqlite_db = sqlite3.connect(app.config['DATABASE'])
#         top.sqlite_db.row_factory = sqlite3.Row
#     return top.sqlite_db


# @app.teardown_appcontext
# def close_database(exception):
#     """Closes the database again at the end of the request."""
#     top = _app_ctx_stack.top
#     if hasattr(top, 'sqlite_db'):
#         top.sqlite_db.close()


# def init_db():
#     """Creates the database tables."""
#     with app.app_context():
#         db = get_db()
#         with app.open_resource('schema.sql', mode='r') as f:
#             db.cursor().executescript(f.read())
#         db.commit()


# def query_db(query, args=(), one=False):
#     """Queries the database and returns a list of dictionaries."""
#     cur = get_db().execute(query, args)
#     rv = cur.fetchall()
#     return (rv[0] if rv else None) if one else rv


def get_user_id(username):
    """Convenience method to look up the id for a username."""
    rv = User.query.filter(User.username == username).first()
    return rv.user_id if rv else None


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.filter(User.user_id == session['user_id']).first()


@app.endpoint('login')
def login():
    """Logs the user in."""
    if g.user:
        return redirect(url_for('timeline'))
    error = None
    if request.method == 'POST':
        user = User.query.filter(User.username == request.form['username']).first()
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user.pw_hash,
                                     request.form['password']):
            error = 'Invalid password'
        else:
            flash('You were logged in')
            session['user_id'] = user.user_id
            return redirect(url_for('timeline'))
    return render_template('rbac/login.html', error=error)


@app.endpoint('register')
def register():
    """Registers the user."""
    if g.user:
        return redirect(url_for('timeline'))
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['email'] or \
                 '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
        elif get_user_id(request.form['username']) is not None:
            error = 'The username is already taken'
        else:
            data = dict([[k, v] for k, v in request.form.items()])

            data['pw_hash'] = generate_password_hash(data['password'])

            del data['password']
            del data['password2']

            db.session.execute(User.__table__.insert(data))
            db.session.commit()

            flash('You were successfully registered and can login now')
            return redirect(url_for('login'))
    return render_template('rbac/register.html', error=error)


@app.endpoint('logout')
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('public_timeline'))
