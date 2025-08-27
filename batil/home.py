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

@bp.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()

    rendered_page = PageHome()
    return(rendered_page.render_page())

# Endpoints for form submissions

@bp.route('/action_pending_challenges', methods=['POST'])
def action_pending_challenges():
    rendered_page = PageHome()
    rendered_page.resolve_action_pending_challenges()
    return(redirect(url_for("home.index")))

@bp.route('/action_existing_games', methods=['POST'])
def action_existing_games():
    rendered_page = PageHome()
    rendered_page.resolve_action_existing_games()
    return(redirect(url_for("home.index")))

@bp.route('/action_new_game', methods=['POST'])
def action_new_game():
    rendered_page = PageHome()
    rendered_page.resolve_action_new_game()
    return(redirect(url_for("home.index")))

