import json

from batil.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.auth import is_logged_in
from batil.db import get_db, get_table_as_list_of_dicts

from batil.action_form import ActionForm
from batil.action_table import ActionTable
from batil.cascade_form import CascadeForm

class PageHome(Page):

    def __init__(self):
        super().__init__()

    def render_content_logged_out(self):
        self.structured_html.append([
            "<header>",
            f"  <h1>Get outta here</h1>",
            "</header>"
        ])


    def render_content_logged_in(self):
        db = get_db()

        self.structured_html.append([
            "<header>",
            f"  <h1>Welcome back, {g.user["username"]}</h1>",
            "</header>"
        ])

        # Pending challenges TODO

        # Existing games
        active_games_dataset = get_table_as_list_of_dicts(f"SELECT GAME_ID, PLAYER_A, PLAYER_B, D_STARTED FROM BOC_GAMES WHERE (PLAYER_A = \"{g.user["username"]}\" OR PLAYER_B = \"{g.user["username"]}\") AND STATUS = \"in_progress\"", ["GAME_ID"], ["PLAYER_A", "PLAYER_B", "D_STARTED"])
        for row in active_games_dataset:
            if row["PLAYER_A"] == g.user["username"]:
                row["OPPONENT"] = row["PLAYER_B"]
            if row["PLAYER_B"] == g.user["username"]:
                row["OPPONENT"] = row["PLAYER_A"]
            del row["PLAYER_A"]
            del row["PLAYER_B"]
        if len(active_games_dataset) > 0:
            form_existing_games = ActionForm("existing_games", "Ongoing games")
            form_existing_games.initialise_tabs(["Your turn", "Waiting for opponent"])
            form_existing_games.open_section(0)
            # Here we make a table listing this user's ACTIVE games

            active_games_table = ActionTable("active_games", include_select = False)
            active_games_table.make_head({"OPPONENT" : "Opponent", "D_STARTED" : "Start date"}, {"open" : "Open game"})
            active_games_table.make_body(active_games_dataset)
            form_existing_games.structured_html.append(active_games_table.structured_html)
            form_existing_games.close_section()

            # Now pending games
            form_existing_games.open_section(1)
            pending_games_dataset = get_table_as_list_of_dicts(f"SELECT GAME_ID, PLAYER_A, PLAYER_B, D_STARTED FROM BOC_GAMES WHERE (PLAYER_A = \"{g.user["username"]}\" OR PLAYER_B = \"{g.user["username"]}\") AND STATUS = \"waiting_for_match\" OR STATUS = \"waiting_for_acceptance\"", ["GAME_ID"], ["PLAYER_A", "PLAYER_B", "D_STARTED"])
            pending_games_table = ActionTable("pending_games", include_select = False)
            pending_games_table.make_head({"PLAYER_A" : "Player A", "PLAYER_B" : "Player B", "D_STARTED" : "Start date"}, {"cancel" : "Cancel game"})
            pending_games_table.make_body(pending_games_dataset)
            form_existing_games.structured_html.append(pending_games_table.structured_html)

            form_existing_games.close_section()
            form_existing_games.close_form()
            self.structured_html.append(form_existing_games.structured_html)



        # New game
        form_new_game = ActionForm("new_game", "New game")
        form_new_game.initialise_tabs(["Rules", "Board", "Opponent"])
        form_new_game.open_section(0)

        select_rules_dataset = get_table_as_list_of_dicts("SELECT RULE AS ID, RULE_GROUP AS \"GROUP\", DESCRIPTION, \"ORDER\", RESTRICTION, REQUIREMENT, LABEL FROM BOC_RULES", ["ID"], ["ID", "GROUP", "DESCRIPTION", "ORDER", "RESTRICTION", "REQUIREMENT", "LABEL"])
        select_rulegroups_dataset = get_table_as_list_of_dicts("SELECT RULE_GROUP AS ID, DESCRIPTION, \"ORDER\" FROM BOC_RULEGROUPS", ["ID"], ["ID", "DESCRIPTION", "ORDER"])
        select_rules_form = CascadeForm("select_rules_form", select_rulegroups_dataset, select_rules_dataset)
        form_new_game.structured_html.append(select_rules_form.structured_html)
        form_new_game.open_section_footer()
        form_new_game.add_button("submit", "start_challenge", "blind_board_blind_opponent", "Create challenge on random board with random opponent")
        form_new_game.close_section()


        # Now: Board choices
        select_board_dataset = get_table_as_list_of_dicts(f"SELECT BOC_BOARDS.BOARD_ID AS BOARD_ID, BOC_BOARDS.BOARD_NAME AS BOARD_NAME, BOC_USER_SAVED_BOARDS.D_SAVED AS D_SAVED, BOC_BOARDS.AUTHOR AS AUTHOR, BOC_BOARDS.D_PUBLISHED AS D_PUBLISHED, BOC_BOARDS.HANDICAP AS HANDICAP FROM BOC_BOARDS INNER JOIN BOC_USER_SAVED_BOARDS ON BOC_BOARDS.BOARD_ID = BOC_USER_SAVED_BOARDS.BOARD_ID AND BOC_USER_SAVED_BOARDS.USERNAME = \"{g.user["username"]}\"", ["BOARD_ID"], ["BOARD_NAME", "D_SAVED", "AUTHOR", "D_PUBLISHED", "HANDICAP"])
        form_new_game.open_section(1)
        select_board_table = ActionTable("select_board_for_new_game")
        select_board_table.make_head({"BOARD_NAME" : "Board", "D_SAVED" : "Saved to library", "AUTHOR" : "Author", "D_PUBLISHED" : "Published", "HANDICAP" : "Handicap"}, {"view" : "View"})
        select_board_table.make_body(select_board_dataset)
        form_new_game.structured_html.append(select_board_table.structured_html)
        form_new_game.open_section_footer()
        form_new_game.add_button("submit", "start_challenge", "blind_opponent", "Create challenge on selected board with random opponent", selection_condition = "action_table_select_board_for_new_game_selected_row_input")
        form_new_game.close_section()

        # Now: opponent choices
        select_opponent_dataset = get_table_as_list_of_dicts(f"SELECT BOC_USER.USERNAME AS USERNAME, BOC_USER.RATING AS RATING, (SELECT COUNT(*) FROM BOC_GAMES WHERE ( (PLAYER_A = {json.dumps(g.user["username"])} AND PLAYER_B = BOC_USER.USERNAME) OR (PLAYER_B = {json.dumps(g.user["username"])} AND PLAYER_A = BOC_USER.USERNAME))) AS COUNT_GAMES FROM BOC_USER INNER JOIN BOC_USER_RELATIONSHIPS ON ((BOC_USER.USERNAME = BOC_USER_RELATIONSHIPS.USER_1 AND BOC_USER_RELATIONSHIPS.USER_2 = {json.dumps(g.user["username"])}) OR (BOC_USER.USERNAME = BOC_USER_RELATIONSHIPS.USER_2 AND BOC_USER_RELATIONSHIPS.USER_1 = {json.dumps(g.user["username"])}))", ["USERNAME"], ["USERNAME", "RATING", "COUNT_GAMES"])
        form_new_game.open_section(2)
        select_opponent_table = ActionTable("select_opponent_for_new_game")
        select_opponent_table.make_head({"USERNAME" : "User", "RATING" : "Rating", "COUNT_GAMES" : "# of games played with you"})
        select_opponent_table.make_body(select_opponent_dataset)
        form_new_game.structured_html.append(select_opponent_table.structured_html)
        form_new_game.open_section_footer()
        form_new_game.add_button("submit", "start_challenge", "targeted_challenge", "Challenge opponent on selected board", selection_condition = f"action_table_select_opponent_for_new_game_selected_row_input")
        form_new_game.close_section(selection_condition = "action_table_select_board_for_new_game_selected_row_input")
        form_new_game.close_form()
        self.structured_html.append(form_new_game.structured_html)


    def render_page(self):
        self.html_open("Home", "style")
        self.html_navbar()

        self.structured_html.append("<section class=\"content\">")
        # Check if logged in
        if g.user:
            self.render_content_logged_in()
        else:
            self.render_content_logged_out()



        self.structured_html.append([
                "</section>"
            ])
        return(self.print_html())
