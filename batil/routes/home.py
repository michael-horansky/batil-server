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

@bp.route('/action_pending_challenges', methods=['POST'])
def action_pending_challenges():
    rendered_page = PageHome()
    rendered_page.resolve_action_pending_challenges()
    return(redirect(url_for("home.index", section=0)))

@bp.route('/action_existing_games', methods=['POST'])
def action_existing_games():
    rendered_page = PageHome()
    rendered_page.resolve_action_existing_games()
    return(redirect(url_for("home.index", section=0)))

@bp.route('/action_new_game', methods=['POST'])
def action_new_game():
    rendered_page = PageHome()
    rendered_page.resolve_action_new_game()
    return(redirect(url_for("home.index", section=0)))

@bp.route('/action_your_boards', methods=['POST'])
def action_your_boards():
    rendered_page = PageHome()
    rendered_page.resolve_action_your_boards()
    return(redirect(url_for("home.index", section=1)))

@bp.route('/action_public_boards', methods=['POST'])
def action_public_boards():
    rendered_page = PageHome()
    get_args = rendered_page.resolve_action_public_boards()
    if get_args is None:
        return(redirect(url_for("home.index", section=2)))
    else:
        return(redirect(url_for("home.index", section=2, **get_args)))

    """if "board_marketplace_table_order" in request.form:
        board_marketplace_table_order_val = request.form.get("board_marketplace_table_order")
        board_marketplace_table_dir_val = request.form.get("board_marketplace_table_dir")
        board_marketplace_table_page_val = request.form.get("board_marketplace_table_page")
        if "action_board_marketplace_table_order" in request.form:
            board_marketplace_table_order_val = request.form.get("action_board_marketplace_table_order")
        if "action_board_marketplace_table_dir" in request.form:
            board_marketplace_table_dir_val = request.form.get("action_board_marketplace_table_dir")
        if "action_board_marketplace_table_page" in request.form:
            page_action = request.form.get("action_board_marketplace_table_page")
            if page_action == "top":
                board_marketplace_table_page_val = 0
            if page_action == "prev":
                board_marketplace_table_page_val -= 1
            if page_action == "next":
                board_marketplace_table_page_val += 1

        # filters
        filter_board_marketplace_table_BOARD_NAME_val = request.form.get("filter_board_marketplace_table_BOARD_NAME")
        filter_board_marketplace_table_AUTHOR_val = request.form.get("filter_board_marketplace_table_AUTHOR")
        filter_board_marketplace_table_D_PUBLISHED_val = request.form.get("filter_board_marketplace_table_D_PUBLISHED")

        return(redirect(url_for("home.index", section=2, board_marketplace_table_order = board_marketplace_table_order_val, board_marketplace_table_dir = board_marketplace_table_dir_val, board_marketplace_table_page = board_marketplace_table_page_val, filter_board_marketplace_table_BOARD_NAME = filter_board_marketplace_table_BOARD_NAME_val, filter_board_marketplace_table_AUTHOR = filter_board_marketplace_table_AUTHOR_val, filter_board_marketplace_table_D_PUBLISHED = filter_board_marketplace_table_D_PUBLISHED_val)))"""


