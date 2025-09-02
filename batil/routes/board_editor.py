# Board editor view for Batil
# For an unpublished board and the owner of the board, this allows the client to edit the board
# For other situations, this is merely to view the board

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from batil.db import get_db, get_table_as_list_of_dicts
from batil.page_board_editor import PageBoardEditor

app = Flask(__name__)

bp = Blueprint('board', __name__, url_prefix="/board")

@bp.route('/<board_id>', methods=['GET'])
def board(board_id):
    rendered_page = PageBoardEditor(board_id)
    return(rendered_page.render_page())

@bp.route('/<board_id>/board_edit_submission', methods=['POST'])
def board_edit_submission(board_id):
    rendered_page = PageBoardEditor(board_id)
    rendered_page.resolve_board_edit_submission()
    return(redirect(url_for("board.board", board_id=board_id)))
    #return(rendered_page.render_page())

