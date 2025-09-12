# Home view for Batil
# For registered users, this contains all of their functionalities: launching games, editing boards, archive, rulebooks etc
# For unregistered users, this contains an introduction and an option to register/log in

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from batil.routes.auth import is_logged_in
from batil.db import get_db

from batil.page_home import PageHome

bp = Blueprint('home', __name__)

@bp.route('/', methods=['GET'])
def index():
    db = get_db()

    rendered_page = PageHome()
    return(rendered_page.render_page())

# Endpoints for form submissions

@bp.route('/action_your_pending_challenges', methods=['POST'])
def action_your_pending_challenges():
    rendered_page = PageHome()
    rendered_page.resolve_action_your_pending_challenges()
    get_args = rendered_page.resolve_dynamic_get_form()
    if get_args is None:
        return(redirect(url_for("home.index", section=0)))
    else:
        return(redirect(url_for("home.index", section=0, **get_args)))

@bp.route('/action_existing_games', methods=['POST'])
def action_existing_games():
    rendered_page = PageHome()
    rendered_page.resolve_action_existing_games()
    get_args = rendered_page.resolve_dynamic_get_form()
    if get_args is None:
        return(redirect(url_for("home.index", section=0)))
    else:
        return(redirect(url_for("home.index", section=0, **get_args)))

@bp.route('/action_new_game', methods=['POST'])
def action_new_game():
    rendered_page = PageHome()
    rendered_page.resolve_action_new_game()
    get_args = rendered_page.resolve_dynamic_get_form()
    if get_args is None:
        return(redirect(url_for("home.index", section=0)))
    else:
        return(redirect(url_for("home.index", section=0, **get_args)))

@bp.route('/action_your_boards', methods=['POST'])
def action_your_boards():
    rendered_page = PageHome()
    rendered_page.resolve_action_your_boards()
    get_args = rendered_page.resolve_dynamic_get_form()
    if get_args is None:
        return(redirect(url_for("home.index", section=1)))
    else:
        return(redirect(url_for("home.index", section=1, **get_args)))

@bp.route('/action_public_boards', methods=['POST'])
def action_public_boards():
    rendered_page = PageHome()
    rendered_page.resolve_action_public_boards()
    get_args = rendered_page.resolve_dynamic_get_form()
    if get_args is None:
        return(redirect(url_for("home.index", section=2)))
    else:
        return(redirect(url_for("home.index", section=2, **get_args)))

@bp.route('/action_users', methods=['POST'])
def action_users():
    rendered_page = PageHome()
    rendered_page.resolve_action_users()
    get_args = rendered_page.resolve_dynamic_get_form()
    if get_args is None:
        return(redirect(url_for("home.index", section=3)))
    else:
        return(redirect(url_for("home.index", section=3, **get_args)))

@bp.route('/action_pending_friend_requests', methods=['POST'])
def action_pending_friend_requests():
    rendered_page = PageHome()
    rendered_page.resolve_action_pending_friend_requests()
    get_args = rendered_page.resolve_dynamic_get_form()
    if get_args is None:
        return(redirect(url_for("home.index", section=4)))
    else:
        return(redirect(url_for("home.index", section=4, **get_args)))

@bp.route('/action_your_profile', methods=['POST'])
def action_your_profile():
    rendered_page = PageHome()
    rendered_page.resolve_action_your_profile()
    get_args = rendered_page.resolve_dynamic_get_form()
    if get_args is None:
        return(redirect(url_for("home.index", section=4)))
    else:
        return(redirect(url_for("home.index", section=4, **get_args)))

@bp.route('/action_tutorial_guide', methods=['POST'])
def action_tutorial_guide():
    rendered_page = PageHome()
    rendered_page.resolve_action_tutorial_guide()
    get_args = rendered_page.resolve_dynamic_get_form()
    if get_args is None:
        return(redirect(url_for("home.index", section=5)))
    else:
        return(redirect(url_for("home.index", section=5, **get_args)))


