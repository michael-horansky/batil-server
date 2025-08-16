import functools
import random
import string

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from batil.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email    = request.form['email']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not email:
            error = 'E-mail is required.'

        if error is None:
            try:
                # Generate authentification code
                length = 32
                random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=length))

                db.execute(
                    "INSERT INTO BOC_USER (USERNAME, EMAIL, PASSWORD, AUTH_CODE, N_FAILS, D_CREATED, D_CHANGED, PRIVILEGE) VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, \'USER\')",
                    (username, email, generate_password_hash(password), random_string),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        db = get_db()

        alluser = db.execute(
            'SELECT * FROM BOC_USER WHERE USERNAME = ?', (username,)
        ).fetchall()
        print("all users:")
        print(alluser)

        error = None
        user = db.execute(
            'SELECT * FROM BOC_USER WHERE USERNAME = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['USERNAME'] = user['USERNAME']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('USERNAME')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM BOC_USER WHERE USERNAME = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def is_logged_in():
    return g.user is not None

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


