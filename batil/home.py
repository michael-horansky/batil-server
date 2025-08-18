# Home view for Batil
# For registered users, this contains all of their functionalities: launching games, editing boards, archive, rulebooks etc
# For unregistered users, this contains an introduction and an option to register/log in

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from batil.auth import is_logged_in
from batil.db import get_db

from batil.page_home import PageHome

bp = Blueprint('home', __name__)

@bp.route('/')
def index():
    db = get_db()

    rendered_page = PageHome()
    return(rendered_page.render_page())

    """if is_logged_in():
        skibidis = db.execute(
            "SELECT USERNAME FROM BOC_USER WHERE USERNAME = ?", (g.user['USERNAME'],)
            ).fetchone()
        return render_template('home/index.html', logged=True, credentials=skibidis)
    else:
        return render_template('home/index.html', logged=False)"""
