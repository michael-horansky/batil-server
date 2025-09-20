# Tutorial editor view for Batil
# For the author, they can edit the tutorial, which means inputting moves for both sides, and adding tutorial comments
# Other users may view the tutorial

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from batil.db import get_db, get_table_as_list_of_dicts
from batil.page_tutorial import PageTutorial

app = Flask(__name__)

bp = Blueprint('tutorial', __name__, url_prefix="/tutorial")

@bp.route('/<tutorial_id>', methods=['GET'])
def tutorial(tutorial_id):
    rendered_page = PageTutorial(tutorial_id)
    return(rendered_page.render_page())

@bp.route('/<tutorial_id>/tutorial_edit_submission', methods=['POST'])
def tutorial_edit_submission(tutorial_id):
    rendered_page = PageTutorial(tutorial_id)
    rendered_page.resolve_tutorial_edit_submission()
    return(redirect(url_for("tutorial.tutorial", tutorial_id=tutorial_id)))
    #return(rendered_page.render_page())

