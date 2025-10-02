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
        get_args.update(ActionTable.get_navigation_keywords("profile_friends", ["USERNAME", "RATING_ROUND", "COUNT_GAMES"]))
        get_args.update(ActionTable.get_navigation_keywords("profile_archive_with_you", ["POV_OUTCOME", "BOARD_NAME", "PLAYER_ROLE", "D_STARTED", "D_FINISHED"]))

        return(get_args)

    def resolve_action_profile_form(self):
        db = get_db()
        for key, val in request.form.items():
            print(f"  {key} --> {val} ({type(val)})")
        if "action_profile_form" in request.form:
            if request.form.get("action_profile_form") == "unfriend":
                unfriend_user(g.user["username"], self.username)
            if request.form.get("action_profile_form") == "withdraw_friend_request":
                withdraw_friend_request(g.user["username"], self.username)
            if request.form.get("action_profile_form") == "accept_friend_request":
                accept_friend_request(g.user["username"], self.username)
            if request.form.get("action_profile_form") == "decline_friend_request":
                decline_friend_request(g.user["username"], self.username)
            if request.form.get("action_profile_form") == "send_friend_request":
                send_friend_request(g.user["username"], self.username)
            if request.form.get("action_profile_form") == "unblock":
                unblock_user(g.user["username"], self.username)
            if request.form.get("action_profile_form") == "block":
                block_user(g.user["username"], self.username)

        elif "action_profile_boards" in request.form:
            action_board_id = int(request.form.get("action_table_profile_boards_selected_row"))
            if request.form.get("action_profile_boards") == "fork":
                db.execute("""
                    INSERT INTO BOC_BOARDS
                        (T_DIM, X_DIM, Y_DIM, STATIC_REPRESENTATION, SETUP_REPRESENTATION, AUTHOR, IS_PUBLIC, D_CREATED, D_CHANGED, HANDICAP, BOARD_NAME,
                        HANDICAP, HANDICAP_STD, KAPPA, STEP_SIZE)
                    SELECT T_DIM, X_DIM, Y_DIM, STATIC_REPRESENTATION, SETUP_REPRESENTATION, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0.0, BOARD_NAME || \" (fork)\",
                        0.0, (SELECT PARAMETER_VALUE FROM BOC_RATING_PARAMETERS WHERE PARAMETER_NAME = \"INITIAL_ESTIMATE_HANDICAP_STD\"),
                        (SELECT 2 * PARAMETER_VALUE / (1 - PARAMETER_VALUE) FROM BOC_RATING_PARAMETERS WHERE PARAMETER_NAME = \"INITIAL_ESTIMATE_DRAW_PROBABILITY\"), 0.0
                    FROM BOC_BOARDS WHERE BOARD_ID = ?""", (g.user["username"], action_board_id))
                db.commit()


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
        number_of_boards_saved = db.execute("SELECT COUNT(*) AS COUNT_BOARDS_SAVED FROM BOC_USER_BOARD_RELATIONSHIPS WHERE USERNAME = ? AND STATUS = \"blocked\"", (self.username,)).fetchone()["COUNT_BOARDS_SAVED"]
        number_of_friends = db.execute("SELECT COUNT(*) AS COUNT_FRIENDS FROM BOC_USER_RELATIONSHIPS WHERE STATUS=\"friends\" AND (USER_1 = ? OR USER_2 = ?)", (self.username, self.username)).fetchone()["COUNT_FRIENDS"]

        stats_table = StaticTable("profile_stats")
        stats_table_cols = ["stats_header", "stats_val"]
        stats_table_data = [
            ["Joined:", self.user_row["D_CREATED"]],
            ["Rating:", self.user_row["RATING_ROUND"]],
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
        if g.user:
            # We determine the relationship between the displayed user and the client
            client_user_relation = db.execute("""
                SELECT
                    MAX(CASE WHEN r.STATUS = 'friends' THEN 1 ELSE 0 END) AS ARE_FRIENDS,
                    MAX(CASE WHEN r.STATUS = 'friends_pending' AND r.USER_1 = :b AND r.USER_2 = :a THEN 1 ELSE 0 END) AS YOUR_REQUEST_PENDING,
                    MAX(CASE WHEN r.STATUS = 'friends_pending' AND r.USER_1 = :a AND r.USER_2 = :b THEN 1 ELSE 0 END) AS THEIR_REQUEST_PENDING,
                    MAX(CASE WHEN r.STATUS = 'blocked' THEN 1 ELSE 0 END) AS ARE_BLOCKED,
                    MAX(CASE WHEN r.STATUS = 'blocked' AND r.USER_1 = :b AND r.USER_2 = :a THEN 1 ELSE 0 END) AS BLOCKED_BY_YOU
                FROM BOC_USER_RELATIONSHIPS r
                WHERE (r.USER_1 = :a AND r.USER_2 = :b) OR (r.USER_1 = :b AND r.USER_2 = :a)
                """, {"a" : self.username, "b" : g.user["USERNAME"]}).fetchone()

            if client_user_relation["ARE_FRIENDS"]:
                profile_form.add_button(0, "submit", "unfriend", "Unfriend", "unfriend")
            elif client_user_relation["YOUR_REQUEST_PENDING"]:
                profile_form.add_button(0, "submit", "withdraw_friend_request", "Withdraw friend request", "withdraw_friend_request")
            elif client_user_relation["THEIR_REQUEST_PENDING"]:
                profile_form.add_button(0, "submit", "accept_friend_request", "Accept friend request", "accept_friend_request")
                profile_form.add_button(0, "submit", "decline_friend_request", "Decline friend request", "decline_friend_request")
            elif not client_user_relation["ARE_BLOCKED"]:
                profile_form.add_button(0, "submit", "send_friend_request", "Send friend request", "send_friend_request")

            if client_user_relation["BLOCKED_BY_YOU"]:
                profile_form.add_button(0, "submit", "unblock", "Unblock", "unblock")
            else:
                profile_form.add_button(0, "submit", "block", "Block", "block")

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
                col_links = {
                    "BOARD_NAME" : (lambda datum : url_for("board.board", board_id = datum["IDENTIFIER"]))
                    },
                rows_per_view = 8
                )

        # Friends
        profile_form.add_ordered_table(3, "profile_friends",
            f"""SELECT BOC_USER.USERNAME AS USERNAME, CAST(ROUND(BOC_USER.RATING) AS INTEGER) AS RATING_ROUND, (SELECT COUNT(*) FROM BOC_GAMES WHERE ( ( (PLAYER_A = {json.dumps(self.username)} AND PLAYER_B = BOC_USER.USERNAME) OR (PLAYER_B = {json.dumps(self.username)} AND PLAYER_A = BOC_USER.USERNAME)) AND STATUS = \"concluded\")) AS COUNT_GAMES FROM BOC_USER INNER JOIN BOC_USER_RELATIONSHIPS ON ((BOC_USER.USERNAME = BOC_USER_RELATIONSHIPS.USER_1 AND BOC_USER_RELATIONSHIPS.USER_2 = {json.dumps(self.username)}) OR (BOC_USER.USERNAME = BOC_USER_RELATIONSHIPS.USER_2 AND BOC_USER_RELATIONSHIPS.USER_1 = {json.dumps(self.username)})) AND BOC_USER_RELATIONSHIPS.STATUS=\"friends\"""",
            "USERNAME", ["USERNAME", "RATING_ROUND", "COUNT_GAMES"],
            include_select = False,
            headers = {"USERNAME" : "User", "RATING_ROUND" : "Rating", "COUNT_GAMES" : "# of games together"},
            order_options = [["COUNT_GAMES", "# games"], ["RATING_ROUND", "Rating"], ["USERNAME", "Username"]],
            actions = {"view" : "View"},
            filters = ["USERNAME", "RATING_ROUND", "COUNT_GAMES"],
            action_instructions = {"view" : {"type" : "link", "url_func" : (lambda datum : url_for("user.user", username = datum["IDENTIFIER"]))}},
            col_links = {
                "USERNAME" : (lambda datum : url_for("user.user", username = datum["USERNAME"]))
                },
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
        self.user_row = db.execute("SELECT USERNAME, D_CREATED, CAST(ROUND(RATING) AS INTEGER) AS RATING_ROUND, PROFILE_PICTURE_EXTENSION FROM BOC_USER WHERE USERNAME = ?", (self.username,)).fetchone()

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
