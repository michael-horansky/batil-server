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

# API endpoints for persistent version checking, form submissions etc
@bp.route("/<regex(\"[A-Za-z0-9]{16}\"):game_id>/moves_count")
def moves_count(game_id):
    client_count = request.args.get("count", type=int, default=0)

    db = get_db()
    current_count = db.execute(
        "SELECT COUNT(*) AS cnt FROM BOC_MOVES WHERE GAME_ID = ?", (game_id,)
    ).fetchone()["cnt"]

    changed = current_count > client_count
    return jsonify({"changed": changed, "count": current_count})
