# Game view for Batil
# For players of the game, this allows them to interact with the game if active
# For other users, unregistered guests, and for all archived games, this allows viewing the game progression and results

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from batil.db import get_db, get_table_as_list_of_dicts
from batil.page_user import PageUser

app = Flask(__name__)

bp = Blueprint('user', __name__, url_prefix="/user")

@bp.route('/<username>', methods=['GET'])
def user(username):
    rendered_page = PageUser(username)
    return(rendered_page.render_page())

# API endpoints for persistent version checking, form submissions etc
