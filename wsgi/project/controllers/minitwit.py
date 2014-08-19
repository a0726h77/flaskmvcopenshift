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
from project.models.message import Message
from project.models.follower import Follower

# configuration
PER_PAGE = 30


def get_user_id(username):
    """Convenience method to look up the id for a username."""
    rv = User.query.filter(User.username == username).first()
    return rv.user_id if rv else None


def format_datetime(timestamp):
    """Format a timestamp for display."""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')


@app.endpoint('timeline')
def timeline():
    """Shows a users timeline or if no user is logged in it will
    redirect to the public timeline.  This timeline shows the user's
    messages as well as all the messages of followed users.
    """
    if not g.user:
        return redirect(url_for('public_timeline'))

    results = db.session.query(Message, User).filter(Message.author_id == User.user_id).filter(db.or_(User.user_id == session['user_id'], User.user_id.in_(Follower.query.with_entities(Follower.whom_id).filter(Follower.who_id == session['user_id'])))).order_by(Message.pub_date.desc()).limit(PER_PAGE)

    return render_template('twit/timeline.html', results=results)


@app.endpoint('public_timeline')
def public_timeline():
    """Displays the latest messages of all users."""
    results = db.session.query(Message, User).filter(Message.author_id == User.user_id).order_by(Message.pub_date.desc()).limit(PER_PAGE)

    return render_template('twit/timeline.html', results=results)


@app.endpoint('user_timeline')
def user_timeline(username):
    """Display's a users tweets."""
    profile_user = User.query.filter(User.username == username).first()
    if profile_user is None:
        abort(404)

    followed = False
    if g.user:
        follower = Follower.query.filter(Follower.who_id == session['user_id']).filter(Follower.whom_id == profile_user.user_id).first()
        if follower:
            followed = True

    results = db.session.query(Message, User).filter(User.user_id == Message.author_id).filter(User.user_id == profile_user.user_id).order_by(Message.pub_date.desc()).limit(PER_PAGE)

    return render_template('twit/timeline.html', results=results, followed=followed, profile_user=profile_user)


@app.endpoint('follow_user')
def follow_user(username):
    """Adds the current user as follower of the given user."""
    if not g.user:
        abort(401)
    whom_id = get_user_id(username)
    if whom_id is None:
        abort(404)

    data = {}
    data['who_id'] = session['user_id']
    data['whom_id'] = whom_id

    db.session.execute(Follower.__table__.insert(data))
    db.session.commit()

    flash('You are now following "%s"' % username)
    return redirect(url_for('user_timeline', username=username))


@app.endpoint('unfollow_user')
def unfollow_user(username):
    """Removes the current user as follower of the given user."""
    if not g.user:
        abort(401)
    whom_id = get_user_id(username)
    if whom_id is None:
        abort(404)

    Follower.query.filter(Follower.who_id == session['user_id']).filter(Follower.whom_id == whom_id).delete()
    db.session.commit()

    flash('You are no longer following "%s"' % username)
    return redirect(url_for('user_timeline', username=username))


@app.endpoint('add_message')
def add_message():
    """Registers a new message for the user."""
    if 'user_id' not in session:
        abort(401)
    if request.form['text']:
        data = {}
        data['author_id'] = session['user_id']
        data['text'] = request.form['text']
        data['pub_date'] = int(time.time())

        db.session.execute(Message.__table__.insert(data))
        db.session.commit()

        flash('Your message was recorded')
    return redirect(url_for('timeline'))


def gravatar_url(email, size=80):
    """Return the gravatar image for the given email address."""
    return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
        (md5(email.strip().lower().encode('utf-8')).hexdigest(), size)


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.filter(User.user_id == session['user_id']).first()


# add some filters to jinja
app.jinja_env.filters['datetimeformat'] = format_datetime
app.jinja_env.filters['gravatar'] = gravatar_url
