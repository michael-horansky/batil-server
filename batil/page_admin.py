import json
import random

from batil.html_objects.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)

from batil.db import get_db, get_pfp_source, send_friend_request, accept_friend_request, decline_friend_request, withdraw_friend_request, unfriend_user, block_user, unblock_user

from batil.aux_funcs import *

from batil.html_objects.action_form import ActionForm
from batil.html_objects.action_table import ActionTable
from batil.html_objects.cascade_form import CascadeForm
from batil.html_objects.static_table import StaticTable

class PageAdmin(Page):

    def __init__(self):
        super().__init__("Admin")

    def resolve_dynamic_get_form(self):
        # Table navigation GET preparation
        get_args = {}
        get_args.update(ActionForm.get_args("system_log_form"))
        get_args.update(ActionTable.get_navigation_keywords("system_logs", ["D_LOGGED", "PRIORITY", "ORIGIN", "MESSAGE"]))
        get_args.update(ActionForm.get_args("rating_model"))
        get_args.update(ActionTable.get_navigation_keywords("housekeeping_logs", ["D_PERFORMED"]))

        return(get_args)

    def resolve_action_system_log_form(self):
        pass

    def resolve_action_rating_model(self):
        pass

    def render_section_system_logs(self):
        system_log_form = ActionForm("system_log_form", "System logs", "admin")
        system_log_form.initialise_tabs(["System logs"])
        system_log_form.add_ordered_table(0, "system_logs", f"""
            SELECT LOG_ID, PRIORITY, ORIGIN, MESSAGE, D_LOGGED
            FROM BOC_SYSTEM_LOGS
            """,
            "LOG_ID", ["D_LOGGED", "PRIORITY", "ORIGIN", "MESSAGE"],
            include_select = False,
            headers = {"D_LOGGED" : "Logged", "PRIORITY" : "Priority", "ORIGIN" : "Origin", "MESSAGE" : "Message"},
            order_options = [["D_LOGGED", "Logged"], ["PRIORITY", "Priority"]],
            filters = ["D_LOGGED", "PRIORITY", "ORIGIN", "MESSAGE"],
            rows_per_view = 8)

        system_log_form.realise_form()
        self.structured_html.append(system_log_form.structured_html)

    def render_section_stats(self):
        self.structured_html.append("<p>statistics about number of users, games, challenges, etc.</p>")

    def render_section_rating_model(self):

        housekeeping_form = ActionForm("rating_model", "Rating model", "admin")
        housekeeping_form.initialise_tabs(["Housekeeping logs", "Trends", "Parameters"])
        housekeeping_form.add_ordered_table(0, "housekeeping_logs", f"""
            SELECT PROCESS_ID, D_PERFORMED, TIME_TAKEN, GAMES_AFFECTED, USERS_AFFECTED, BOARDS_AFFECTED, GAMES_TOTAL, USERS_TOTAL, BOARDS_TOTAL
            FROM BOC_HOUSEKEEPING_LOGS
            """,
            "PROCESS_ID", ["D_PERFORMED", "TIME_TAKEN", "GAMES_AFFECTED", "USERS_AFFECTED", "BOARDS_AFFECTED", "GAMES_TOTAL", "USERS_TOTAL", "BOARDS_TOTAL"],
            include_select = False,
            headers = {"D_PERFORMED" : "Performed", "TIME_TAKEN" : "Time", "GAMES_AFFECTED" : "G. aff.", "USERS_AFFECTED" : "U. aff.", "BOARDS_AFFECTED" : "B. aff.", "GAMES_TOTAL" : "G. tot.", "USERS_TOTAL" : "U. tot.", "BOARDS_TOTAL" : "B. tot."},
            order_options = [["D_PERFORMED", "Perf."], ["TIME_TAKEN", "Time"], ["GAMES_AFFECTED", "G. aff."], ["USERS_AFFECTED", "U. aff."], ["BOARDS_AFFECTED", "B. aff."]],
            filters = ["D_PERFORMED"],
            rows_per_view = 8)

        housekeeping_form.realise_form()
        self.structured_html.append(housekeeping_form.structured_html)

    def render_content_logged_in(self):
        self.initialise_sections({"system_logs" : "System logs", "stats" : "Stats", "rating_model" : "Rating model"})
        self.render_section_system_logs()
        self.open_next_section()
        self.render_section_stats()
        self.open_next_section()
        self.render_section_rating_model()
        self.close_sections()

    def render_content_logged_out(self):
        self.structured_html.append([
            "<h1>You don't have the right, O you don't have the right</h1>",
            "<h1>You don't have the right, O you don't have the right</h1>"
            ])

    def render_page(self):

        # username, pfp, stats (rating, number of games played), archive of all games, list of friends
        db = get_db()

        self.html_open("admin_style")
        self.html_navbar()

        # Check if logged in and has admin priviliges
        if g.user:
            client_privilege = db.execute("SELECT PRIVILEGE FROM BOC_USER WHERE USERNAME = ?", (g.user["username"],)).fetchone()["PRIVILEGE"]
            if client_privilege == "ADMIN":
                self.render_content_logged_in()
        else:
            self.open_container("logged_out_main_content")
            self.open_container("logged_out_main_column")
            self.open_container("logged_out_profile_content", "logged_out_main_column_section")
            self.render_content_logged_out()
            self.close_container()
            self.close_container()
            self.close_container()

        return(self.print_html())
