# Admin access point for Batil
# Better to use a scalpel rather than touch the incision with greasy fingers

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from batil.db import get_db
from batil.page_admin import PageAdmin

app = Flask(__name__)

bp = Blueprint('admin', __name__, url_prefix="/admin")

@bp.route('/', methods=['GET'])
def admin():
    rendered_page = PageAdmin()
    return(rendered_page.render_page())

# API endpoints for persistent version checking, form submissions etc
@bp.route('/action_system_log_form', methods=['POST'])
def action_system_log_form():
    rendered_page = PageAdmin()
    rendered_page.resolve_action_system_log_form()
    get_args = rendered_page.resolve_dynamic_get_form()
    if get_args is None:
        return(redirect(url_for("admin.admin", section=0)))
    else:
        return(redirect(url_for("admin.admin", section=0, **get_args)))

@bp.route('/action_rating_model', methods=['POST'])
def action_rating_model():
    rendered_page = PageAdmin()
    rendered_page.resolve_action_rating_model()
    get_args = rendered_page.resolve_dynamic_get_form()
    if get_args is None:
        return(redirect(url_for("admin.admin", section=2)))
    else:
        return(redirect(url_for("admin.admin", section=2, **get_args)))
