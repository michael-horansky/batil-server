import json
import random

from batil.html_objects.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)

from batil.db import get_db, get_table_as_list_of_dicts, new_blind_challenge, new_targeted_challenge, accept_challenge, decline_challenge

from batil.aux_funcs import *

from batil.html_objects.action_form import ActionForm
from batil.html_objects.action_table import ActionTable
from batil.html_objects.cascade_form import CascadeForm

class PageUser(Page):

    def __init__(self, username):
        super().__init__("User")
        self.username = username

    def resolve_request(self):
        if request.method == 'POST':
            # We check what action is happening
            for key, val in request.form.items():
                print(f"  {key} --> {val} ({type(val)})")

    def resolve_dynamic_get_form(self):
        # Table navigation GET preparation
        get_args = {}

        return(get_args)

    def render_profile_header(self):
        # pfp
        if self.user_row["PROFILE_PICTURE_EXTENSION"] is not None:
            pfp_ext_ind = int(self.user_row["PROFILE_PICTURE_EXTENSION"])
            pfp_url = url_for('static', filename=f"user_content/profile_pictures/{self.username}_pfp{PFP_EXTENSIONS[pfp_ext_ind]}")
            self.structured_html.append([
                f"<img src=\"{pfp_url}\" alt=\"{self.username} profile picture\">"
                ])

    def render_content_logged_in(self):
        # Add features: send friend request, block, archive of games with you
        self.render_content_logged_out()


    def render_content_logged_out(self):
        # username, pfp, stats (rating, number of games played), archive of all games, list of friends
        db = get_db()
        self.user_row = db.execute("SELECT USERNAME, D_CREATED, RATING, PROFILE_PICTURE_EXTENSION FROM BOC_USER WHERE USERNAME = ?", (self.username,)).fetchone()

        self.open_container("main_content")
        self.open_container("main_column")

        self.open_container("profile_header", "main_column_section")
        self.render_profile_header()
        self.close_container()

        self.close_container()
        self.close_container()


    def render_page(self):
        self.resolve_request()
        self.html_open("user_style")
        self.html_navbar()

        # Check if logged in
        if g.user:
            self.render_content_logged_in()
        else:
            self.structured_html.append("<section class=\"content\">")
            self.render_content_logged_out()
            self.structured_html.append("</section>")



        return(self.print_html())
