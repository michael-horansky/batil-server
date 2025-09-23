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

@bp.route('/<int:tutorial_id>', defaults={"editor_role" : None}, methods=['GET'])
@bp.route('/<int:tutorial_id>/<editor_role>', methods=['GET'])
def tutorial(tutorial_id, editor_role):
    if editor_role not in [None, "A", "B"]:
        return(redirect(url_for("tutorial.tutorial", tutorial_id=tutorial_id)))
    rendered_page = PageTutorial(tutorial_id, editor_role)
    if rendered_page.client_role != "editor" and editor_role is not None:
        return(redirect(url_for("tutorial.tutorial", tutorial_id=tutorial_id)))
    rendered_page.load_game()
    return(rendered_page.render_page())
    return jsonify({"changed": changed})

@bp.route("/<int:tutorial_id>/<editor_role>/command_submission", methods=["POST"])
def command_submission(tutorial_id, editor_role):
    rendered_page = PageTutorial(tutorial_id, editor_role)
    rendered_page.load_game()
    last_turn_index = rendered_page.gm.current_turn_index
    rendered_page.resolve_command_submission()
    return(redirect(url_for("tutorial.tutorial", tutorial_id=tutorial_id, editor_role=editor_role, last_displayed_turn = last_turn_index)))

@bp.route('/<tutorial_id>/tutorial_edit_tutorial_comments', defaults={"editor_role" : None}, methods=['POST'])
@bp.route('/<tutorial_id>/<editor_role>/tutorial_edit_tutorial_comments', methods=['POST'])
def tutorial_edit_tutorial_comments(tutorial_id, editor_role):
    rendered_page = PageTutorial(tutorial_id, editor_role)
    rendered_page.load_game()
    rendered_page.resolve_tutorial_comments_edit()
    active_turn_index = int(request.form.get("turn_index"))
    return(redirect(url_for("tutorial.tutorial", tutorial_id=tutorial_id, editor_role=editor_role, last_displayed_turn = active_turn_index)))
    #return(rendered_page.render_page())

