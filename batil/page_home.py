import json
import random

from batil.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.auth import is_logged_in
from batil.db import get_db, get_table_as_list_of_dicts, new_blind_challenge, new_targeted_challenge, accept_challenge, decline_challenge

from batil.aux_funcs import *

from batil.action_form import ActionForm
from batil.action_table import ActionTable
from batil.cascade_form import CascadeForm

class PageHome(Page):

    def __init__(self):
        super().__init__()

    def resolve_request(self):
        db = get_db()
        if request.method == 'POST':
            # We check what action is happening
            for key, val in request.form.items():
                print(f"  {key} --> {val} ({type(val)})")

            # There has to exist a key which is equal to action_{identifier} of one of the elements of the page
            # The value associated specifies which button within this element sent the request
            if request.form.get("action_pending_challenges") is not None:
                if request.form.get("action_pending_challenges") == "accept":
                    print("Accept this challenge!")
                    accept_challenge(int(request.form.get("action_table_pending_challenges_selected_row")))

                elif request.form.get("action_pending_challenges") == "view_board":
                    print("View the board!")
                elif request.form.get("action_pending_challenges") == "decline":
                    print("Decline this challenge!")
                    decline_challenge(int(request.form.get("action_table_pending_challenges_selected_row")))

            if request.form.get("action_active_games") is not None:
                if request.form.get("action_active_games") == "open":
                    print("Open this ongoing game!")

            if request.form.get("action_new_game") is not None:
                if request.form.get("action_new_game") == "blind_board_blind_opponent":
                    print("New challenge: blind board, blind opponent!")
                    ruleset_selection = {}
                    all_rulegroups_raw = db.execute("SELECT RULE_GROUP FROM BOC_RULEGROUPS").fetchall()
                    all_rulegroups = []
                    for rulegroup_row in all_rulegroups_raw:
                        if request.form.get(rulegroup_row["RULE_GROUP"]) is None:
                            raise Exception("Missing selection in ruleset table")
                        else:
                            ruleset_selection[rulegroup_row["RULE_GROUP"]] = request.form.get(rulegroup_row["RULE_GROUP"])

                    new_blind_challenge(None, g.user["username"], ruleset_selection)


                elif request.form.get("action_new_game") == "blind_opponent":
                    print("New challenge: blind opponent!")
                    ruleset_selection = {}
                    all_rulegroups_raw = db.execute("SELECT RULE_GROUP FROM BOC_RULEGROUPS").fetchall()
                    all_rulegroups = []
                    for rulegroup_row in all_rulegroups_raw:
                        if request.form.get(rulegroup_row["RULE_GROUP"]) is None:
                            raise Exception("Missing selection in ruleset table")
                        else:
                            ruleset_selection[rulegroup_row["RULE_GROUP"]] = request.form.get(rulegroup_row["RULE_GROUP"])

                    new_blind_challenge(int(request.form.get("action_table_select_board_for_new_game_selected_row")), g.user["username"], ruleset_selection)
                elif request.form.get("action_new_game") == "targeted_challenge":
                    print("New challenge: targeted!")
                    ruleset_selection = {}
                    all_rulegroups_raw = db.execute("SELECT RULE_GROUP FROM BOC_RULEGROUPS").fetchall()
                    all_rulegroups = []
                    for rulegroup_row in all_rulegroups_raw:
                        if request.form.get(rulegroup_row["RULE_GROUP"]) is None:
                            raise Exception("Missing selection in ruleset table")
                        else:
                            ruleset_selection[rulegroup_row["RULE_GROUP"]] = request.form.get(rulegroup_row["RULE_GROUP"])

                    new_targeted_challenge(int(request.form.get("action_table_select_board_for_new_game_selected_row")), request.form.get("action_table_select_opponent_for_new_game_selected_row"), g.user["username"], ruleset_selection)

            if request.form.get("action_select_board_for_new_game") is not None:
                if request.form.get("action_select_board_for_new_game") == "view":
                    print("View the board before you make a challenge outta it!")

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
        #pending_challenges_dataset = get_table_as_list_of_dicts(f"SELECT BOC_GAMES.GAME_ID AS GAME_ID, BOC_GAMES.PLAYER_A AS PLAYER_A, BOC_GAMES.PLAYER_B AS PLAYER_B, BOC_BOARDS.BOARD_NAME, BOC_GAMES.D_CHALLENGE FROM BOC_GAMES INNER JOIN BOC_BOARDS ON BOC_GAMES.BOARD_ID = BOC_BOARDS.BOARD_ID WHERE (BOC_GAMES.STATUS = \"waiting_for_acceptance\" AND (BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])} OR BOC_GAMES.PLAYER_B = {json.dumps(g.user["username"])}))", ["GAME_ID"])
        pending_challenges_dataset = get_table_as_list_of_dicts(f"SELECT BOC_CHALLENGES.CHALLENGE_ID AS CHALLENGE_ID, BOC_CHALLENGES.CHALLENGER AS CHALLENGER, BOC_CHALLENGES.DATE_CREATED AS DATE_CREATED, BOC_BOARDS.BOARD_NAME AS BOARD_NAME FROM BOC_CHALLENGES LEFT JOIN BOC_BOARDS ON BOC_CHALLENGES.BOARD_ID = BOC_BOARDS.BOARD_ID WHERE BOC_CHALLENGES.STATUS = 'active' AND BOC_CHALLENGES.CHALLENGEE = {json.dumps(g.user["username"])}", "CHALLENGE_ID", ["CHALLENGER", "BOARD_NAME", "DATE_CREATED"]) # WHERE BOC_CHALLENGES.CHALLENGEE = {json.dumps(g.user["username"])}
        if len(pending_challenges_dataset) > 0:
            form_pending_challenges = ActionForm("pending_challenges", "Challenges for you")
            form_pending_challenges.initialise_tabs(["Incoming challenges"])
            form_pending_challenges.open_section(0)
            pending_challenges_table = ActionTable("pending_challenges", include_select = False)
            pending_challenges_table.make_head({"CHALLENGER" : "Challenger", "BOARD_NAME" : "Board", "DATE_CREATED" : "Date"}, {"accept" : "Accept", "view_board" : "View board", "decline" : "Decline"})
            pending_challenges_table.make_body(pending_challenges_dataset)
            form_pending_challenges.structured_html.append(pending_challenges_table.structured_html)
            form_pending_challenges.close_section()

            form_pending_challenges.close_form()
            self.structured_html.append(form_pending_challenges.structured_html)


        # Existing games
        #active_games_dataset = get_table_as_list_of_dicts(f"SELECT GAME_ID, PLAYER_A, PLAYER_B, D_STARTED FROM BOC_GAMES WHERE (PLAYER_A = \"{g.user["username"]}\" OR PLAYER_B = \"{g.user["username"]}\") AND STATUS = \"in_progress\"", "GAME_ID", ["PLAYER_A", "PLAYER_B", "D_STARTED"])
        active_games_not_your_turn = get_table_as_list_of_dicts(f"""
                WITH latest AS (
                    SELECT BOC_MOVES.GAME_ID, MAX(BOC_MOVES.TURN_INDEX) AS max_turn
                    FROM BOC_MOVES
                    GROUP BY BOC_MOVES.GAME_ID
                ),
                latest_moves AS (
                    SELECT BOC_MOVES.GAME_ID, GROUP_CONCAT(BOC_MOVES.PLAYER) AS players_at_latest
                    FROM BOC_MOVES
                    JOIN latest L ON L.GAME_ID = BOC_MOVES.GAME_ID AND L.max_turn = BOC_MOVES.TURN_INDEX
                    GROUP BY BOC_MOVES.GAME_ID
                )
                SELECT BOC_GAMES.GAME_ID AS GAME_ID, BOC_GAMES.PLAYER_A AS PLAYER_A, BOC_GAMES.PLAYER_B AS PLAYER_B, BOC_GAMES.D_STARTED AS D_STARTED
                FROM BOC_GAMES JOIN latest_moves LM ON LM.GAME_ID = BOC_GAMES.GAME_ID
                WHERE
                    (BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])} OR BOC_GAMES.PLAYER_B = {json.dumps(g.user["username"])})
                    AND BOC_GAMES.STATUS = \"in_progress\"
                    AND (
                        (BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])} AND LM.players_at_latest = 'A')
                        OR
                        (BOC_GAMES.PLAYER_B = {json.dumps(g.user["username"])} AND LM.players_at_latest = 'B')
                    )
                ORDER BY D_STARTED
            """, "GAME_ID", ["PLAYER_A", "PLAYER_B", "D_STARTED"])
        active_games_your_turn = get_table_as_list_of_dicts(f"""
                WITH latest AS (
                    SELECT BOC_MOVES.GAME_ID, MAX(BOC_MOVES.TURN_INDEX) AS max_turn
                    FROM BOC_MOVES
                    GROUP BY BOC_MOVES.GAME_ID
                ),
                latest_moves AS (
                    SELECT BOC_MOVES.GAME_ID, GROUP_CONCAT(BOC_MOVES.PLAYER) AS players_at_latest
                    FROM BOC_MOVES
                    JOIN latest L ON L.GAME_ID = BOC_MOVES.GAME_ID AND L.max_turn = BOC_MOVES.TURN_INDEX
                    GROUP BY BOC_MOVES.GAME_ID
                )
                SELECT BOC_GAMES.GAME_ID AS GAME_ID, BOC_GAMES.PLAYER_A AS PLAYER_A, BOC_GAMES.PLAYER_B AS PLAYER_B, BOC_GAMES.D_STARTED AS D_STARTED
                FROM BOC_GAMES JOIN latest_moves LM ON LM.GAME_ID = BOC_GAMES.GAME_ID
                WHERE
                    (BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])} OR BOC_GAMES.PLAYER_B = {json.dumps(g.user["username"])})
                    AND BOC_GAMES.STATUS = \"in_progress\"
                    AND NOT (
                        (BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])} AND LM.players_at_latest = 'A')
                        OR
                        (BOC_GAMES.PLAYER_B = {json.dumps(g.user["username"])} AND LM.players_at_latest = 'B')
                    )
                ORDER BY D_STARTED
            """, "GAME_ID", ["PLAYER_A", "PLAYER_B", "D_STARTED"])
        for row in active_games_your_turn:
            if row["PLAYER_A"] == g.user["username"]:
                row["OPPONENT"] = row["PLAYER_B"]
            if row["PLAYER_B"] == g.user["username"]:
                row["OPPONENT"] = row["PLAYER_A"]
            del row["PLAYER_A"]
            del row["PLAYER_B"]
        for row in active_games_not_your_turn:
            if row["PLAYER_A"] == g.user["username"]:
                row["OPPONENT"] = row["PLAYER_B"]
            if row["PLAYER_B"] == g.user["username"]:
                row["OPPONENT"] = row["PLAYER_A"]
            del row["PLAYER_A"]
            del row["PLAYER_B"]

        if len(active_games_your_turn) == 0 and len(active_games_not_your_turn) == 0:
            self.structured_html.append("<h2 class=\"empty_form_placeholder\">No ongoing games</h2>")
        else:
            active_game_headers = []
            if len(active_games_your_turn) > 0:
                active_game_headers.append("Your turn")
            if len(active_games_not_your_turn) > 0:
                active_game_headers.append("Waiting for opponent")
            form_existing_games = ActionForm("existing_games", "Ongoing games")
            form_existing_games.initialise_tabs(active_game_headers)
            sections_initialised = 0
            if len(active_games_your_turn) > 0:
                form_existing_games.open_section(sections_initialised)
                sections_initialised += 1
                active_games_your_turn_table = ActionTable("active_games_your_turn", include_select = False)
                active_games_your_turn_table.make_head({"OPPONENT" : "Opponent", "D_STARTED" : "Start date"}, {"open" : "Open game"}, action_instructions = {
                        "open" : {"type" : "link", "url_func" : (lambda x : url_for("game_bp.game", game_id = x))}
                    })
                active_games_your_turn_table.make_body(active_games_your_turn)
                form_existing_games.structured_html.append(active_games_your_turn_table.structured_html)
                form_existing_games.close_section()
            if len(active_games_not_your_turn) > 0:
                form_existing_games.open_section(sections_initialised)
                sections_initialised += 1
                active_games_not_your_turn_table = ActionTable("active_games_not_your_turn", include_select = False)
                active_games_not_your_turn_table.make_head({"OPPONENT" : "Opponent", "D_STARTED" : "Start date"}, {"open" : "Open game"}, action_instructions = {
                        "open" : {"type" : "link", "url_func" : (lambda x : url_for("game_bp.game", game_id = x))}
                    })
                active_games_not_your_turn_table.make_body(active_games_not_your_turn)
                form_existing_games.structured_html.append(active_games_not_your_turn_table.structured_html)
                form_existing_games.close_section()
            form_existing_games.close_form()
            self.structured_html.append(form_existing_games.structured_html)




        # New game
        form_new_game = ActionForm("new_game", "New game")
        form_new_game.initialise_tabs(["Rules", "Board", "Opponent"])
        form_new_game.open_section(0)

        select_rules_dataset = get_table_as_list_of_dicts("SELECT RULE AS ID, RULE_GROUP AS \"GROUP\", DESCRIPTION, \"ORDER\", RESTRICTION, REQUIREMENT, LABEL FROM BOC_RULES", "ID", ["ID", "GROUP", "DESCRIPTION", "ORDER", "RESTRICTION", "REQUIREMENT", "LABEL"])
        select_rulegroups_dataset = get_table_as_list_of_dicts("SELECT RULE_GROUP AS ID, DESCRIPTION, \"ORDER\" FROM BOC_RULEGROUPS", "ID", ["ID", "DESCRIPTION", "ORDER"])
        select_rules_form = CascadeForm("select_rules_form", select_rulegroups_dataset, select_rules_dataset)
        form_new_game.structured_html.append(select_rules_form.structured_html)
        form_new_game.open_section_footer()
        form_new_game.add_button("submit", "blind_board_blind_opponent", "Create challenge on random board with random opponent")
        form_new_game.close_section()


        # Now: Board choices
        select_board_dataset = get_table_as_list_of_dicts(f"SELECT BOC_BOARDS.BOARD_ID AS BOARD_ID, BOC_BOARDS.BOARD_NAME AS BOARD_NAME, BOC_USER_SAVED_BOARDS.D_SAVED AS D_SAVED, BOC_BOARDS.AUTHOR AS AUTHOR, BOC_BOARDS.D_PUBLISHED AS D_PUBLISHED, BOC_BOARDS.HANDICAP AS HANDICAP FROM BOC_BOARDS INNER JOIN BOC_USER_SAVED_BOARDS ON BOC_BOARDS.BOARD_ID = BOC_USER_SAVED_BOARDS.BOARD_ID AND BOC_USER_SAVED_BOARDS.USERNAME = \"{g.user["username"]}\"", "BOARD_ID", ["BOARD_NAME", "D_SAVED", "AUTHOR", "D_PUBLISHED", "HANDICAP"])
        form_new_game.open_section(1)
        select_board_table = ActionTable("select_board_for_new_game")
        select_board_table.make_head({"BOARD_NAME" : "Board", "D_SAVED" : "Saved to library", "AUTHOR" : "Author", "D_PUBLISHED" : "Published", "HANDICAP" : "Handicap"}, {"view" : "View"})
        select_board_table.make_body(select_board_dataset)
        form_new_game.structured_html.append(select_board_table.structured_html)
        form_new_game.open_section_footer()
        form_new_game.add_button("submit", "blind_opponent", "Create challenge on selected board with random opponent", selection_condition = "action_table_select_board_for_new_game_selected_row_input")
        form_new_game.close_section()

        # Now: opponent choices
        select_opponent_dataset = get_table_as_list_of_dicts(f"SELECT BOC_USER.USERNAME AS USERNAME, BOC_USER.RATING AS RATING, (SELECT COUNT(*) FROM BOC_GAMES WHERE ( ( (PLAYER_A = {json.dumps(g.user["username"])} AND PLAYER_B = BOC_USER.USERNAME) OR (PLAYER_B = {json.dumps(g.user["username"])} AND PLAYER_A = BOC_USER.USERNAME)) AND STATUS = \"concluded\")) AS COUNT_GAMES FROM BOC_USER INNER JOIN BOC_USER_RELATIONSHIPS ON ((BOC_USER.USERNAME = BOC_USER_RELATIONSHIPS.USER_1 AND BOC_USER_RELATIONSHIPS.USER_2 = {json.dumps(g.user["username"])}) OR (BOC_USER.USERNAME = BOC_USER_RELATIONSHIPS.USER_2 AND BOC_USER_RELATIONSHIPS.USER_1 = {json.dumps(g.user["username"])}))", "USERNAME", ["USERNAME", "RATING", "COUNT_GAMES"])
        form_new_game.open_section(2)
        select_opponent_table = ActionTable("select_opponent_for_new_game")
        select_opponent_table.make_head({"USERNAME" : "User", "RATING" : "Rating", "COUNT_GAMES" : "# of games played with you"})
        select_opponent_table.make_body(select_opponent_dataset)
        form_new_game.structured_html.append(select_opponent_table.structured_html)
        form_new_game.open_section_footer()
        form_new_game.add_button("submit", "targeted_challenge", "Challenge opponent on selected board", selection_condition = f"action_table_select_opponent_for_new_game_selected_row_input")
        form_new_game.close_section(selection_condition = "action_table_select_board_for_new_game_selected_row_input")
        form_new_game.close_form()
        self.structured_html.append(form_new_game.structured_html)


    def render_page(self):
        self.resolve_request()
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
