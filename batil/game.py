# Game view for Batil
# For players of the game, this allows them to interact with the game if active
# For other users, unregistered guests, and for all archived games, this allows viewing the game progression and results

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from batil.page_game import PageGame

app = Flask(__name__)

bp = Blueprint('game_bp', __name__, url_prefix="/game")

@bp.route('/<regex("[A-Za-z0-9]{16}"):game_id>', methods=['GET', 'POST'])
def game(game_id):
    rendered_page = PageGame(game_id)
    return(rendered_page.render_page())
