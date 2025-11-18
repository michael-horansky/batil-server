import json
import random

from batil.html_objects.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)

from batil.db import get_db, get_table_as_list_of_dicts, create_new_tutorial

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
        get_args.update(ActionForm.get_args("new_tutorial"))
        get_args.update(ActionTable.get_navigation_keywords("select_board_for_new_tutorial", ["BOARD_NAME"]))
        get_args.update(ActionForm.get_args("edit_tutorials"))
        get_args.update(ActionTable.get_navigation_keywords("your_tutorials", ["BOARD_NAME"]))

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

    def resolve_action_new_tutorial(self):
        db = get_db()
        if "action_new_tutorial" in request.form:
            if request.form.get("action_new_tutorial") == "create_tutorial":
                ruleset_selection = {}
                all_rulegroups_raw = db.execute("SELECT RULE_GROUP FROM BOC_RULEGROUPS").fetchall()
                all_rulegroups = []
                for rulegroup_row in all_rulegroups_raw:
                    if request.form.get(rulegroup_row["RULE_GROUP"]) is None:
                        raise Exception("Missing selection in ruleset table")
                    else:
                        ruleset_selection[rulegroup_row["RULE_GROUP"]] = request.form.get(rulegroup_row["RULE_GROUP"])
                selected_board_id = int(request.form.get("action_table_select_board_for_new_tutorial_selected_row"))
                create_new_tutorial(g.user["username"], selected_board_id, ruleset_selection)

    def resolve_action_edit_tutorials(self):
        pass

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

    def render_section_tutorials(self):
        # Here you can make tutorials for any of your boards (they don't have to be public)
        db = get_db()

        # Create a new tutorial

        new_tutorial_form = ActionForm("new_tutorial", "New tutorial", "admin")
        new_tutorial_form.initialise_tabs(["Select rules", "Select board"])

        select_rules_dataset = get_table_as_list_of_dicts("SELECT RULE AS ID, RULE_GROUP AS \"GROUP\", DESCRIPTION, \"ORDER\", RESTRICTION, REQUIREMENT, LABEL FROM BOC_RULES", "ID", ["ID", "GROUP", "DESCRIPTION", "ORDER", "RESTRICTION", "REQUIREMENT", "LABEL"])
        select_rulegroups_dataset = get_table_as_list_of_dicts("SELECT RULE_GROUP AS ID, DESCRIPTION, \"ORDER\" FROM BOC_RULEGROUPS", "ID", ["ID", "DESCRIPTION", "ORDER"])
        select_rules_form = CascadeForm("select_rules_form", select_rulegroups_dataset, select_rules_dataset)
        new_tutorial_form.add_to_tab(0, "content", select_rules_form.structured_html)

        new_tutorial_form.add_ordered_table(1, "select_board_for_new_tutorial",
            f"""SELECT BOARD_ID, BOARD_NAME
            FROM BOC_BOARDS
            WHERE AUTHOR = {json.dumps(g.user["username"])}""",
            "BOARD_ID", ["BOARD_NAME"],
            include_select = True,
            headers = {"BOARD_NAME" : "Board"},
            order_options = [["BOARD_NAME", "Board"]],
            actions = {"view" : "View"},
            filters = ["BOARD_NAME"],
            action_instructions = {"view" : {"type" : "link", "url_func" : (lambda datum : url_for("board.board", board_id = datum["IDENTIFIER"]))}},
            rows_per_view = 6
            )

        new_tutorial_form.add_button(1, "submit", "create_tutorial", "Create new tutorial", selection_condition = "action_table_select_board_for_new_tutorial_selected_row_input")

        new_tutorial_form.realise_form()
        self.structured_html.append(new_tutorial_form.structured_html)

        # Edit existing tutorials

        edit_tutorials_form = ActionForm("edit_tutorials", "Edit tutorials", "admin")
        edit_tutorials_form.initialise_tabs(["Your tutorials"])
        # TODO also number of moves
        edit_tutorials_form.add_ordered_table(0, "your_tutorials", f"""
            SELECT BOC_TUTORIALS.TUTORIAL_ID AS TUTORIAL_ID, BOC_BOARDS.BOARD_NAME AS BOARD_NAME, BOC_BOARDS.BOARD_ID AS BOARD_ID, BOC_TUTORIALS.STATUS AS STATUS, BOC_TUTORIALS.OUTCOME AS OUTCOME, BOC_TUTORIALS.D_CREATED AS D_CREATED, BOC_TUTORIALS.D_CHANGED AS D_CHANGED
            FROM BOC_TUTORIALS
                INNER JOIN BOC_BOARDS ON BOC_BOARDS.BOARD_ID = BOC_TUTORIALS.BOARD_ID
            WHERE BOC_TUTORIALS.AUTHOR = {json.dumps(g.user["username"])}
            """,
            "TUTORIAL_ID", ["BOARD_ID", "BOARD_NAME", "STATUS", "OUTCOME", "D_CREATED", "D_CHANGED"],
            include_select = False,
            headers = {"BOARD_NAME" : "Board", "STATUS" : "Status", "OUTCOME" : "O.", "D_CREATED" : "Created", "D_CHANGED" : "Changed"},
            order_options = [["D_CHANGED", "Changed"], ["D_CREATED", "Created"]],
            actions = {"edit" : "Edit"},
            action_instructions = {"edit" : {"type" : "link", "url_func" : (lambda datum : url_for("tutorial.tutorial", tutorial_id = datum["IDENTIFIER"]))}},
            col_links = {"BOARD_NAME" : (lambda datum : url_for("board.board", board_id = datum["BOARD_ID"]))},
            filters = ["BOARD_NAME"],
            rows_per_view = 8)

        edit_tutorials_form.realise_form()
        self.structured_html.append(edit_tutorials_form.structured_html)


    def render_content_logged_in(self):
        self.initialise_sections({"system_logs" : "System logs", "stats" : "Stats", "rating_model" : "Rating model", "tutorials" : "Tutorials"})
        self.render_section_system_logs()
        self.open_next_section()
        self.render_section_stats()
        self.open_next_section()
        self.render_section_rating_model()
        self.open_next_section()
        self.render_section_tutorials()
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
