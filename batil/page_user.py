import json
import random

from batil.html_objects.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)

from batil.db import get_db, get_table_as_list_of_dicts, new_blind_challenge, new_targeted_challenge, accept_challenge, decline_challenge, get_pfp_source

from batil.aux_funcs import *

from batil.html_objects.action_form import ActionForm
from batil.html_objects.action_table import ActionTable
from batil.html_objects.cascade_form import CascadeForm
from batil.html_objects.static_table import StaticTable

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

        get_args.update(ActionForm.get_args("profile_form"))
        get_args.update(ActionTable.get_navigation_keywords("profile_archive", ["OPPONENT", "POV_OUTCOME", "BOARD_NAME", "PLAYER_ROLE", "D_STARTED", "D_FINISHED"]))
        get_args.update(ActionTable.get_navigation_keywords("profile_boards", ["BOARD_NAME", "D_PUBLISHED"]))
        get_args.update(ActionTable.get_navigation_keywords("profile_friends", ["USERNAME", "RATING", "COUNT_GAMES"]))
        get_args.update(ActionTable.get_navigation_keywords("profile_archive_with_you", ["POV_OUTCOME", "BOARD_NAME", "PLAYER_ROLE", "D_STARTED", "D_FINISHED"]))

        return(get_args)

    def resolve_action_profile_form(self):
        pass

    def render_profile_header(self):
        pfp_url = get_pfp_source(self.username)
        self.structured_html.append([
            f"<img src=\"{pfp_url}\" alt=\"{self.username} profile picture\">",
            f"<div id=\"profile_header_username\">{ self.username }</div>",
            ])

    def render_profile_content(self):
        db = get_db()
        profile_form = ActionForm("profile_form", f"{self.username}: profile", "user", username = self.username)
        profile_form_tabs = ["Stats", "Archive", "Boards", "Friends"]
        if g.user:
            # logged in
            if g.user["username"] != self.username:
                profile_form_tabs.append("Games with you")

        profile_form.initialise_tabs(profile_form_tabs)

        # Stats
        pfp_url = get_pfp_source(self.username)
        business_card = [
            f"<div id=\"profile_head\">",
            f"  <img src=\"{pfp_url}\" alt=\"{self.username}'s profile picture\" class=\"profile_picture\">",
            f"  <div class=\"profile_picture_tag\">{self.username}</div>",
            f"</div>"
            ]


        number_of_games = db.execute("SELECT COUNT(*) AS COUNT_GAMES FROM BOC_GAMES WHERE STATUS=\"concluded\" AND (PLAYER_A = ? OR PLAYER_B = ?)", (self.username, self.username)).fetchone()["COUNT_GAMES"]
        number_of_boards = db.execute("SELECT COUNT(*) AS COUNT_BOARDS FROM BOC_BOARDS WHERE IS_PUBLIC=1 AND AUTHOR = ?", (self.username,)).fetchone()["COUNT_BOARDS"]
        number_of_boards_saved = db.execute("SELECT COUNT(*) AS COUNT_BOARDS_SAVED FROM BOC_USER_SAVED_BOARDS WHERE USERNAME = ?", (self.username,)).fetchone()["COUNT_BOARDS_SAVED"]
        number_of_friends = db.execute("SELECT COUNT(*) AS COUNT_FRIENDS FROM BOC_USER_RELATIONSHIPS WHERE STATUS=\"friends\" AND (USER_1 = ? OR USER_2 = ?)", (self.username, self.username)).fetchone()["COUNT_FRIENDS"]

        stats_table = StaticTable("profile_stats")
        stats_table_cols = ["stats_header", "stats_val"]
        stats_table_data = [
            ["Joined:", self.user_row["D_CREATED"]],
            ["Rating:", self.user_row["RATING"]],
            ["Played:", number_of_games],
            ["Boards:", number_of_boards],
            ["Boards saved:", number_of_boards_saved],
            ["Friends:", number_of_friends]
            ]
        stats_table.make_table(stats_table_data, stats_table_cols)

        profile_stats = [
            "<div id=\"business_card\">",
            business_card,
            stats_table.structured_html,
            "</div>"
            ]

        profile_form.add_to_tab(0, "content", profile_stats)
        #profile_form.add_to_tab(0, "content", stats_table.structured_html)

        # Archive
        profile_form.add_game_archive(1, "profile_archive", self.username, rows_per_view = 8)

        # Boards
        boards_actions = {"view" : "View"}
        if g.user:
            # Logged in means you can fork
            boards_actions["fork"] = "Fork"
        profile_form.add_ordered_table(2, "profile_boards",
                f"""SELECT BOC_BOARDS.BOARD_ID as BOARD_ID, BOC_BOARDS.BOARD_NAME AS BOARD_NAME, BOC_BOARDS.D_PUBLISHED AS D_PUBLISHED, BOC_BOARDS.HANDICAP AS HANDICAP, COUNT(BOC_GAMES.BOARD_ID) AS GAMES_PLAYED
                    FROM BOC_BOARDS LEFT JOIN BOC_GAMES ON BOC_GAMES.BOARD_ID = BOC_BOARDS.BOARD_ID AND BOC_GAMES.STATUS = \"concluded\"
                    WHERE BOC_BOARDS.AUTHOR = {json.dumps(self.username)} AND BOC_BOARDS.IS_PUBLIC = 1 GROUP BY BOC_BOARDS.BOARD_ID""",
                "BOARD_ID", ["BOARD_NAME", "D_PUBLISHED", "GAMES_PLAYED", "HANDICAP"],
                include_select = False,
                headers = {"BOARD_NAME" : "Board", "D_PUBLISHED" : "Published", "GAMES_PLAYED" : "# games played", "HANDICAP" : "Handicap"},
                order_options = [["D_PUBLISHED", "Published"], ["GAMES_PLAYED", "# games"]],
                actions = boards_actions,
                filters = ["BOARD_NAME", "D_PUBLISHED"],
                action_instructions = {"view" : {"type" : "link", "url_func" : (lambda datum : url_for("board.board", board_id = datum["IDENTIFIER"]))}},
                rows_per_view = 8
                )

        # Friends
        profile_form.add_ordered_table(3, "profile_friends",
            f"""SELECT BOC_USER.USERNAME AS USERNAME, BOC_USER.RATING AS RATING, (SELECT COUNT(*) FROM BOC_GAMES WHERE ( ( (PLAYER_A = {json.dumps(self.username)} AND PLAYER_B = BOC_USER.USERNAME) OR (PLAYER_B = {json.dumps(self.username)} AND PLAYER_A = BOC_USER.USERNAME)) AND STATUS = \"concluded\")) AS COUNT_GAMES FROM BOC_USER INNER JOIN BOC_USER_RELATIONSHIPS ON ((BOC_USER.USERNAME = BOC_USER_RELATIONSHIPS.USER_1 AND BOC_USER_RELATIONSHIPS.USER_2 = {json.dumps(self.username)}) OR (BOC_USER.USERNAME = BOC_USER_RELATIONSHIPS.USER_2 AND BOC_USER_RELATIONSHIPS.USER_1 = {json.dumps(self.username)})) AND BOC_USER_RELATIONSHIPS.STATUS=\"friends\"""",
            "USERNAME", ["USERNAME", "RATING", "COUNT_GAMES"],
            include_select = False,
            headers = {"USERNAME" : "User", "RATING" : "Rating", "COUNT_GAMES" : "# of games together"},
            order_options = [["COUNT_GAMES", "# games"], ["RATING", "Rating"], ["USERNAME", "Username"]],
            actions = {"view" : "View"},
            filters = ["USERNAME", "RATING", "COUNT_GAMES"],
            action_instructions = {"view" : {"type" : "link", "url_func" : (lambda datum : url_for("user.user", username = datum["IDENTIFIER"]))}},
            rows_per_view = 8,
            enforce_filter_kw = "WHERE")

        # Games with you
        if g.user:
            if g.user["username"] != self.username:
                profile_form.add_game_archive(4, "profile_archive_with_you", self.username, g.user["username"], rows_per_view = 8)


        profile_form.realise_form()
        self.structured_html.append(profile_form.structured_html)


    def render_page(self):
        self.resolve_request()
        self.html_open("user_style")
        self.html_navbar()

        # username, pfp, stats (rating, number of games played), archive of all games, list of friends
        db = get_db()
        self.user_row = db.execute("SELECT USERNAME, D_CREATED, RATING, PROFILE_PICTURE_EXTENSION FROM BOC_USER WHERE USERNAME = ?", (self.username,)).fetchone()

        self.open_container("main_content")
        self.open_container("main_column")

        #self.open_container("profile_header", "main_column_section")
        #self.render_profile_header()
        #self.close_container()

        self.open_container("profile_content", "main_column_section")
        self.render_profile_content()
        self.close_container()

        self.close_container()
        self.close_container()



        return(self.print_html())
