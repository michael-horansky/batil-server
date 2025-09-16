import json
import random

from batil.html_objects.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.security import generate_password_hash
from PIL import Image
import os


from batil.db import get_db, get_table_as_list_of_dicts, new_blind_challenge, new_targeted_challenge, accept_challenge, decline_challenge, send_friend_request, accept_friend_request, decline_friend_request, withdraw_friend_request, unfriend_user, block_user, unblock_user, hide_board, tdv_edit_chapter, tdv_add_chapter, tdv_add_child

from batil.aux_funcs import *

from batil.html_objects.action_form import ActionForm
from batil.html_objects.action_table import ActionTable
from batil.html_objects.cascade_form import CascadeForm
from batil.html_objects.tree_document_viewer import TreeDocumentViewer

class PageHome(Page):

    def __init__(self):
        super().__init__("Home")

        board_template_file = current_app.open_resource("database/board_template.json")
        self.board_template = json.load(board_template_file)
        board_template_file.close()

    def resolve_request(self):
        if request.method == 'POST':
            # We check what action is happening
            for key, val in request.form.items():
                print(f"  {key} --> {val} ({type(val)})")

    def resolve_dynamic_get_form(self):
        # Table navigation GET preparation
        get_args = {}
        # Play
        get_args.update(ActionForm.get_args("new_game", ["select_board_for_new_game"]))
        get_args.update(ActionTable.get_navigation_keywords("select_board_for_new_game", ["BOARD_NAME", "AUTHOR", "D_SAVED"]))
        get_args.update(ActionTable.get_navigation_keywords("select_opponent_for_new_game", ["USERNAME"]))
        get_args.update(ActionForm.get_args("your_pending_challenges"))
        get_args.update(ActionTable.get_navigation_keywords("pending_challenges"))
        get_args.update(ActionForm.get_args("existing_games"))
        get_args.update(ActionTable.get_navigation_keywords("active_games_your_turn"))
        get_args.update(ActionTable.get_navigation_keywords("active_games_not_your_turn"))
        # Your boards
        get_args.update(ActionForm.get_args("your_boards"))
        get_args.update(ActionTable.get_navigation_keywords("your_boards_unpublished", ["BOARD_NAME"]))
        get_args.update(ActionTable.get_navigation_keywords("your_boards_published", ["BOARD_NAME"]))
        # Public boards
        get_args.update(ActionForm.get_args("public_boards"))
        get_args.update(ActionTable.get_navigation_keywords("board_marketplace_table", ["BOARD_NAME", "AUTHOR", "D_PUBLISHED"]))
        get_args.update(ActionTable.get_navigation_keywords("your_saved_boards", ["BOARD_NAME", "AUTHOR", "D_PUBLISHED", "D_SAVED"]))
        # Users
        get_args.update(ActionForm.get_args("users"))
        get_args.update(ActionTable.get_navigation_keywords("leaderboard", ["USERNAME", "RATING", "COUNT_GAMES"]))
        # Profile
        get_args.update(ActionForm.get_args("pending_friend_requests"))
        get_args.update(ActionTable.get_navigation_keywords("friend_requests_for_you", ["USER_1", "D_STATUS"]))
        get_args.update(ActionForm.get_args("your_profile"))
        get_args.update(ActionTable.get_navigation_keywords("your_archive", ["OPPONENT", "POV_OUTCOME", "BOARD_NAME", "PLAYER_ROLE", "D_STARTED", "D_FINISHED"]))
        get_args.update(ActionTable.get_navigation_keywords("your_friends", ["USERNAME", "RATING", "COUNT_GAMES"]))
        get_args.update(ActionTable.get_navigation_keywords("your_blocked", ["USERNAME", "RATING", "COUNT_GAMES"]))
        # Tutorials
        get_args.update(TreeDocumentViewer.get_navigation_keywords("tutorial_guide"))

        return(get_args)

    def resolve_action_your_pending_challenges(self):
        if request.form.get("action_pending_challenges") == "accept":
            print("Accept this challenge!")
            accept_challenge(int(request.form.get("action_table_pending_challenges_selected_row")))
        elif request.form.get("action_pending_challenges") == "decline":
            print("Decline this challenge!")
            decline_challenge(int(request.form.get("action_table_pending_challenges_selected_row")))

    def resolve_action_existing_games(self):
        pass

    def resolve_action_new_game(self):
        db = get_db()
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

    def resolve_action_your_boards(self):
        db = get_db()
        if "action_your_boards" in request.form.keys():
            # The form buttons were interacted with
            if request.form.get("action_your_boards") == "create_new_board":
                # Create a new element in BOC_BOARDS and also open the board in editor in new tab
                # The new board is set to the default board
                db.execute("INSERT INTO BOC_BOARDS (T_DIM, X_DIM, Y_DIM, STATIC_REPRESENTATION, SETUP_REPRESENTATION, AUTHOR, IS_PUBLIC, D_CREATED, D_CHANGED, HANDICAP, BOARD_NAME) VALUES (?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0.0, ?)", (self.board_template["T_DIM"], self.board_template["X_DIM"], self.board_template["Y_DIM"], self.board_template["STATIC_REPRESENTATION"], self.board_template["SETUP_REPRESENTATION"], g.user["username"], self.board_template["BOARD_NAME"]))
                db.commit()
        elif "action_your_boards_unpublished" in request.form.keys():
            # row action on an unpublished board
            action_board_id = int(request.form.get("action_table_your_boards_unpublished_selected_row"))
            if request.form.get("action_your_boards_unpublished") == "delete":
                db.execute("DELETE FROM BOC_BOARDS WHERE BOARD_ID = ?", (action_board_id,))
                db.commit()
            elif request.form.get("action_your_boards_unpublished") == "publish":
                db.execute("UPDATE BOC_BOARDS SET IS_PUBLIC = 1, D_PUBLISHED = CURRENT_TIMESTAMP WHERE BOARD_ID = ?", (action_board_id,))
                db.execute("INSERT INTO BOC_USER_SAVED_BOARDS (BOARD_ID, USERNAME, D_SAVED) VALUES (?, ?, CURRENT_TIMESTAMP)", (action_board_id, g.user["username"]))
                db.commit()
        elif "action_your_boards_published" in request.form.keys():
            action_board_id = int(request.form.get("action_table_your_boards_published_selected_row"))
            if request.form.get("action_your_boards_published") == "hide":
                # published boards are always shown from BOC_USER_SAVED_BOARDS, this just deletes the relational line
                hide_board(g.user["username"], action_board_id)
            elif request.form.get("action_your_boards_published") == "fork":
                db.execute("INSERT INTO BOC_BOARDS (T_DIM, X_DIM, Y_DIM, STATIC_REPRESENTATION, SETUP_REPRESENTATION, AUTHOR, IS_PUBLIC, D_CREATED, D_CHANGED, HANDICAP, BOARD_NAME) SELECT T_DIM, X_DIM, Y_DIM, STATIC_REPRESENTATION, SETUP_REPRESENTATION, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0.0, BOARD_NAME || \" (fork)\" FROM BOC_BOARDS WHERE BOARD_ID = ?", (g.user["username"], action_board_id))
                db.commit()


        # Default action: return back
        return(redirect(url_for("home.index", section=1)))

    def resolve_action_public_boards(self):
        db = get_db()

        # Database manipulation
        if "action_board_marketplace_table" in request.form:
            if request.form.get("action_board_marketplace_table") == "save":
                # The user saves a board to their collection
                saved_board_id = int(request.form.get("action_table_board_marketplace_table_selected_row"))
                relevant_row = db.execute("SELECT BOARD_ID, D_SAVED FROM BOC_USER_SAVED_BOARDS WHERE BOARD_ID = ? AND USERNAME = ?", (saved_board_id, g.user["username"])).fetchone()
                if relevant_row is None:
                    # We create a new row
                    db.execute("INSERT INTO BOC_USER_SAVED_BOARDS (BOARD_ID, USERNAME, D_SAVED) VALUES (?, ?, CURRENT_TIMESTAMP)", (saved_board_id, g.user["username"]))
                else:
                    # We update the existing row
                    db.execute("UPDATE BOC_USER_SAVED_BOARDS SET D_SAVED = CURRENT_TIMESTAMP WHERE BOARD_ID = ? AND USERNAME = ?", (saved_board_id, g.user["username"]))
                db.commit()
        if "action_your_saved_boards" in request.form:
            if request.form.get("action_your_saved_boards") == "remove":
                # The user removes a board from their collection
                removed_board_id = int(request.form.get("action_table_your_saved_boards_selected_row"))
                db.execute("DELETE FROM BOC_USER_SAVED_BOARDS WHERE BOARD_ID = ? AND USERNAME = ?", (removed_board_id, g.user["username"]))
                db.commit()

    def resolve_action_users(self):
        db = get_db()
        for k, v in request.form.items():
            print(f" {k} -> {v}")
        # Database manipulation
        if "action_leaderboard" in request.form:
            action_username = request.form.get("action_table_leaderboard_selected_row")
            if request.form.get("action_leaderboard") == "send_friend_request":
                send_friend_request(g.user["username"], action_username)
            elif request.form.get("action_leaderboard") == "accept_friend_request":
                accept_friend_request(g.user["username"], action_username)
            if request.form.get("action_leaderboard") == "withdraw_friend_request":
                withdraw_friend_request(g.user["username"], action_username)
            if request.form.get("action_leaderboard") == "unfriend":
                unfriend_user(g.user["username"], action_username)
            if request.form.get("action_leaderboard") == "block_user":
                block_user(g.user["username"], action_username)
            if request.form.get("action_leaderboard") == "unblock_user":
                unblock_user(g.user["username"], action_username)

    def resolve_action_pending_friend_requests(self):
        db = get_db()
        for k, v in request.form.items():
            print(f" {k} -> {v}")
        if "action_friend_requests_for_you" in request.form:
            action_username = request.form.get("action_table_friend_requests_for_you_selected_row")
            if request.form.get("action_friend_requests_for_you") == "accept":
                accept_friend_request(g.user["username"], action_username)
            elif request.form.get("action_friend_requests_for_you") == "decline":
                decline_friend_request(g.user["username"], action_username)


    def resolve_action_your_profile(self):
        db = get_db()
        # Database manipulation
        if "action_your_profile" in request.form:
            if request.form.get("action_your_profile") == "save_changes":

                # First, we check if profile picture was uploaded
                if "new_profile_picture" in request.files:
                    pfp_file = request.files.get("new_profile_picture")
                    pfp_ext = get_file_extension(pfp_file)
                    if pfp_ext is not None:
                        save_path = os.path.join(current_app.root_path, "static", "user_content", "profile_pictures", f"{g.user["username"]}_pfp{PFP_EXTENSIONS[pfp_ext]}")
                        pfp_img = Image.open(pfp_file)
                        pfp_img.thumbnail((256, 256))
                        pfp_img.save(save_path, quality=85)
                        db.execute("UPDATE BOC_USER SET PROFILE_PICTURE_EXTENSION = ? WHERE USERNAME = ?", (pfp_ext, g.user["username"]))
                        db.commit()

                # Now we check if the language selection changed
                print(f"Language setting changed to {request.form.get("user_language_select")}")

                # Now to see if the password changed
                if request.form.get("new_password") != "" and request.form.get("new_password") == request.form.get("new_password_confirm"):
                    db.execute("UPDATE BOC_USER SET PASSWORD = ? WHERE USERNAME = ?", (generate_password_hash(request.form.get("new_password")), g.user["username"]))
                    db.commit()

        if "action_your_friends" in request.form:
            action_username = request.form.get("action_table_your_friends_selected_row")
            if request.form.get("action_your_friends") == "unfriend":
                unfriend_user(g.user["username"], action_username)
        if "action_your_blocked" in request.form:
            action_username = request.form.get("action_table_your_blocked_selected_row")
            if request.form.get("action_your_blocked") == "unblock":
                unblock_user(g.user["username"], action_username)

    def resolve_action_tutorial_guide(self):
        if "tutorial_guide_action" in request.form:
            action_chapter = int(request.form.get("tutorial_guide_chapter"))
            if request.form.get("tutorial_guide_action") == "edit":
                tdv_edit_chapter(action_chapter, request.form.get("chapter_label"), request.form.get("chapter_content"))
            if request.form.get("tutorial_guide_action") == "insert_new_chapter_next":
                tdv_add_chapter(action_chapter)
            if request.form.get("tutorial_guide_action") == "insert_new_child":
                tdv_add_child(action_chapter)

    def render_content_logged_out(self):
        tutorial_guide = TreeDocumentViewer("tutorial_guide", "home", "index", "GUEST")

        self.structured_html.append(tutorial_guide.structured_html)

    def render_section_play(self):
        db = get_db()

        self.open_container("play_forms_container")



        # New game
        form_new_game = ActionForm("new_game", "New game", "home")
        form_new_game.initialise_tabs(["Rules", "Board", "Opponent"])

        select_rules_dataset = get_table_as_list_of_dicts("SELECT RULE AS ID, RULE_GROUP AS \"GROUP\", DESCRIPTION, \"ORDER\", RESTRICTION, REQUIREMENT, LABEL FROM BOC_RULES", "ID", ["ID", "GROUP", "DESCRIPTION", "ORDER", "RESTRICTION", "REQUIREMENT", "LABEL"])
        select_rulegroups_dataset = get_table_as_list_of_dicts("SELECT RULE_GROUP AS ID, DESCRIPTION, \"ORDER\" FROM BOC_RULEGROUPS", "ID", ["ID", "DESCRIPTION", "ORDER"])
        select_rules_form = CascadeForm("select_rules_form", select_rulegroups_dataset, select_rules_dataset)

        form_new_game.add_to_tab(0, "content", select_rules_form.structured_html)
        form_new_game.add_button(0, "submit", "blind_board_blind_opponent", "Create challenge on random board with random opponent")


        # Now: Board choices
        form_new_game.add_ordered_table(1, "select_board_for_new_game",
            f"""SELECT BOC_BOARDS.BOARD_ID AS BOARD_ID, BOC_BOARDS.BOARD_NAME AS BOARD_NAME, BOC_USER_SAVED_BOARDS.D_SAVED AS D_SAVED, BOC_BOARDS.AUTHOR AS AUTHOR, BOC_BOARDS.HANDICAP AS HANDICAP, COUNT(BOC_GAMES.BOARD_ID) AS GAMES_PLAYED
            FROM BOC_BOARDS
                LEFT JOIN BOC_GAMES ON BOC_GAMES.BOARD_ID = BOC_BOARDS.BOARD_ID AND BOC_GAMES.STATUS = \"concluded\"
                INNER JOIN BOC_USER_SAVED_BOARDS ON BOC_BOARDS.BOARD_ID = BOC_USER_SAVED_BOARDS.BOARD_ID AND BOC_USER_SAVED_BOARDS.USERNAME = \"{g.user["username"]}\"
                GROUP BY BOC_BOARDS.BOARD_ID""",
            "BOARD_ID", ["BOARD_NAME", "AUTHOR", "D_SAVED", "GAMES_PLAYED", "HANDICAP"],
            include_select = True,
            headers = {"BOARD_NAME" : "Board", "AUTHOR" : "Author", "D_SAVED" : "Saved to library", "GAMES_PLAYED" : "# of games", "HANDICAP" : "Handicap"},
            order_options = [["D_SAVED", "Saved"]],
            actions = {"view" : "View"},
            filters = ["BOARD_NAME", "AUTHOR", "D_SAVED"],
            action_instructions = {"view" : {"type" : "link", "url_func" : (lambda datum : url_for("board.board", board_id = datum["IDENTIFIER"]))}},
            col_links = {
                "BOARD_NAME" : (lambda datum : url_for("board.board", board_id = datum["IDENTIFIER"])),
                "AUTHOR" : (lambda datum : url_for("user.user", username = datum["AUTHOR"]))
                },
            rows_per_view = 6
            )

        form_new_game.add_button(1, "submit", "blind_opponent", "Create challenge on selected board with random opponent", selection_condition = "action_table_select_board_for_new_game_selected_row_input")

        # Now: opponent choices
        # This tab only shows if a board was chosen in previous tab
        form_new_game.set_tab_property(2, "selection_condition", "action_table_select_board_for_new_game_selected_row_input")

        form_new_game.add_ordered_table(2, "select_opponent_for_new_game",
            f"SELECT BOC_USER.USERNAME AS USERNAME, BOC_USER.RATING AS RATING, (SELECT COUNT(*) FROM BOC_GAMES WHERE ( ( (PLAYER_A = {json.dumps(g.user["username"])} AND PLAYER_B = BOC_USER.USERNAME) OR (PLAYER_B = {json.dumps(g.user["username"])} AND PLAYER_A = BOC_USER.USERNAME)) AND STATUS = \"concluded\")) AS COUNT_GAMES FROM BOC_USER INNER JOIN BOC_USER_RELATIONSHIPS ON ((BOC_USER.USERNAME = BOC_USER_RELATIONSHIPS.USER_1 AND BOC_USER_RELATIONSHIPS.USER_2 = {json.dumps(g.user["username"])}) OR (BOC_USER.USERNAME = BOC_USER_RELATIONSHIPS.USER_2 AND BOC_USER_RELATIONSHIPS.USER_1 = {json.dumps(g.user["username"])})) AND BOC_USER_RELATIONSHIPS.STATUS=\"friends\"",
            "USERNAME", ["USERNAME", "RATING", "COUNT_GAMES"],
            include_select = True,
            headers = {"USERNAME" : "User", "RATING" : "Rating", "COUNT_GAMES" : "# of games played with you"},
            order_options = [["COUNT_GAMES", "# games"]],
            actions = {"view" : "View"},
            action_instructions = {"view" : {"type" : "link", "url_func" : (lambda datum : url_for("user.user", username = datum["IDENTIFIER"]))}},
            col_links = {"USERNAME" : (lambda datum : url_for("user.user", username = datum["IDENTIFIER"]))},
            filters = ["USERNAME"],
            rows_per_view = 6
            )

        #form_new_game.add_to_tab(2, "content", select_opponent_table.structured_html)
        form_new_game.add_button(2, "submit", "targeted_challenge", "Challenge opponent on selected board", selection_condition = f"action_table_select_opponent_for_new_game_selected_row_input")

        form_new_game.realise_form()
        self.structured_html.append(form_new_game.structured_html)

        self.open_container("play_forms_right")

        # Pending challenges
        pending_challenges_sample = db.execute(f"SELECT CHALLENGE_ID FROM BOC_CHALLENGES WHERE BOC_CHALLENGES.STATUS = 'active' AND BOC_CHALLENGES.CHALLENGEE = ? LIMIT 1", (g.user["username"],)).fetchone()
        if pending_challenges_sample is not None:
            form_pending_challenges = ActionForm("your_pending_challenges", "Challenges for you", "home")
            form_pending_challenges.initialise_tabs(["Incoming challenges"])

            form_pending_challenges.add_ordered_table(0, "pending_challenges",
                f"SELECT BOC_CHALLENGES.CHALLENGE_ID AS CHALLENGE_ID, BOC_CHALLENGES.CHALLENGER AS CHALLENGER, BOC_CHALLENGES.DATE_CREATED AS DATE_CREATED, BOC_BOARDS.BOARD_NAME AS BOARD_NAME, BOC_BOARDS.BOARD_ID AS BOARD_ID FROM BOC_CHALLENGES LEFT JOIN BOC_BOARDS ON BOC_CHALLENGES.BOARD_ID = BOC_BOARDS.BOARD_ID WHERE BOC_CHALLENGES.STATUS = 'active' AND BOC_CHALLENGES.CHALLENGEE = {json.dumps(g.user["username"])}",
                "CHALLENGE_ID", ["CHALLENGER", "BOARD_NAME", "DATE_CREATED", "BOARD_ID"],
                include_select = False,
                headers = {"CHALLENGER" : "Challenger", "BOARD_NAME" : "Board", "DATE_CREATED" : "Date"},
                order_options = [["DATE_CREATED", "Date"]],
                actions = {"accept" : "Accept", "decline" : "Decline"},
                filters = False,
                col_links = {
                    "CHALLENGER" : (lambda datum : url_for("user.user", username = datum["CHALLENGER"])),
                    "BOARD_NAME" : (lambda datum : url_for("board.board", board_id = datum["BOARD_ID"]))
                    },
                rows_per_view = 3
                )

            form_pending_challenges.realise_form()
            self.structured_html.append(form_pending_challenges.structured_html)


        # Existing games
        active_games_not_your_turn_sample = db.execute(
            f"""
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
                SELECT
                    BOC_GAMES.GAME_ID
                FROM
                    BOC_GAMES
                    JOIN latest_moves LM ON LM.GAME_ID = BOC_GAMES.GAME_ID
                WHERE
                    (BOC_GAMES.PLAYER_A = ? OR BOC_GAMES.PLAYER_B = ?)
                    AND BOC_GAMES.STATUS = \"in_progress\"
                    AND (
                        (BOC_GAMES.PLAYER_A = ? AND LM.players_at_latest = 'A')
                        OR
                        (BOC_GAMES.PLAYER_B = ? AND LM.players_at_latest = 'B')
                    )
                LIMIT 1
            """, (g.user["username"], g.user["username"], g.user["username"], g.user["username"])
            ).fetchone()
        active_games_your_turn_sample = db.execute(
            f"""
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
                SELECT
                    BOC_GAMES.GAME_ID
                FROM BOC_GAMES JOIN latest_moves LM ON LM.GAME_ID = BOC_GAMES.GAME_ID
                WHERE
                    (BOC_GAMES.PLAYER_A = ? OR BOC_GAMES.PLAYER_B = ?)
                    AND BOC_GAMES.STATUS = \"in_progress\"
                    AND NOT (
                        (BOC_GAMES.PLAYER_A = ? AND LM.players_at_latest = 'A')
                        OR
                        (BOC_GAMES.PLAYER_B = ? AND LM.players_at_latest = 'B')
                    )
                LIMIT 1
            """, (g.user["username"], g.user["username"], g.user["username"], g.user["username"])
            ).fetchone()

        if active_games_not_your_turn_sample is None and active_games_your_turn_sample is None:
            self.structured_html.append("<h2 class=\"empty_form_placeholder\">No ongoing games</h2>")
        else:
            active_game_headers = []
            if active_games_your_turn_sample is not None:
                active_game_headers.append("Your turn")
            if active_games_not_your_turn_sample is not None:
                active_game_headers.append("Waiting for opponent")
            form_existing_games = ActionForm("existing_games", "Ongoing games", "home")
            form_existing_games.initialise_tabs(active_game_headers)
            sections_initialised = 0
            if active_games_your_turn_sample is not None:
                form_existing_games.add_ordered_table(sections_initialised, "active_games_your_turn",
                    f"""
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
                    ), rules AS (
                        SELECT GAME_ID, RULE AS deadline_rule
                        FROM BOC_RULESETS
                        WHERE RULE_GROUP = 'deadline'
                    )
                    SELECT
                        BOC_GAMES.GAME_ID AS GAME_ID,
                        CASE
                            WHEN BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])} THEN BOC_GAMES.PLAYER_B
                            ELSE BOC_GAMES.PLAYER_A
                        END AS OPPONENT,
                        BOC_GAMES.D_STARTED AS D_STARTED,
                        BOC_BOARDS.BOARD_ID AS BOARD_ID,
                        BOC_BOARDS.BOARD_NAME AS BOARD_NAME,
                        CASE
                            WHEN rules.deadline_rule = 'no_deadline'
                                THEN NULL
                            WHEN rules.deadline_rule = 'one_day_per_move'
                                THEN 86400 - COALESCE(
                                    strftime('%s','now') - strftime('%s',
                                        CASE WHEN BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])}
                                            THEN BOC_GAMES.PLAYER_A_PROMPTED
                                            ELSE BOC_GAMES.PLAYER_B_PROMPTED END
                                    ), 0
                                )
                            WHEN rules.deadline_rule = 'three_days_per_move'
                                THEN 259200 - COALESCE(
                                    strftime('%s','now') - strftime('%s',
                                        CASE WHEN BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])}
                                            THEN BOC_GAMES.PLAYER_A_PROMPTED
                                            ELSE BOC_GAMES.PLAYER_B_PROMPTED END
                                    ), 0
                                )
                            WHEN rules.deadline_rule = 'one_hour_cumulative'
                                THEN (CASE WHEN BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])}
                                        THEN BOC_GAMES.PLAYER_A_CUMULATIVE_SECONDS
                                        ELSE BOC_GAMES.PLAYER_B_CUMULATIVE_SECONDS END)
                                    - COALESCE(
                                        strftime('%s','now') - strftime('%s',
                                            CASE WHEN BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])}
                                                THEN BOC_GAMES.PLAYER_A_PROMPTED
                                                ELSE BOC_GAMES.PLAYER_B_PROMPTED END
                                        ), 0
                                    )
                            WHEN rules.deadline_rule = 'one_day_cumulative'
                                THEN (CASE WHEN BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])}
                                        THEN BOC_GAMES.PLAYER_A_CUMULATIVE_SECONDS
                                        ELSE BOC_GAMES.PLAYER_B_CUMULATIVE_SECONDS END)
                                    - COALESCE(
                                        strftime('%s','now') - strftime('%s',
                                            CASE WHEN BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])}
                                                THEN BOC_GAMES.PLAYER_A_PROMPTED
                                                ELSE BOC_GAMES.PLAYER_B_PROMPTED END
                                        ), 0
                                    )
                            ELSE NULL
                        END AS TIME_LEFT_SECONDS
                    FROM
                        BOC_GAMES
                        JOIN latest_moves LM ON LM.GAME_ID = BOC_GAMES.GAME_ID
                        INNER JOIN BOC_BOARDS ON BOC_GAMES.BOARD_ID = BOC_BOARDS.BOARD_ID
                        JOIN rules ON rules.GAME_ID = BOC_GAMES.GAME_ID
                    WHERE
                        (BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])} OR BOC_GAMES.PLAYER_B = {json.dumps(g.user["username"])})
                        AND BOC_GAMES.STATUS = \"in_progress\"
                        AND NOT (
                            (BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])} AND LM.players_at_latest = 'A')
                            OR
                            (BOC_GAMES.PLAYER_B = {json.dumps(g.user["username"])} AND LM.players_at_latest = 'B')
                        )
                    """, "GAME_ID", ["OPPONENT", "BOARD_NAME", "TIME_LEFT_SECONDS", "D_STARTED", "BOARD_ID"],
                    include_select = False,
                    headers = {"OPPONENT" : "Opponent", "BOARD_NAME" : "Board", "TIME_LEFT_SECONDS" : "Time left", "D_STARTED" : "Start date"},
                    order_options = [["D_STARTED", "Start"]],
                    actions = {"open" : "Open game"},
                    filters = False,
                    action_instructions = {"open" : {"type" : "link", "url_func" : (lambda datum : url_for("game_bp.game", game_id = datum["IDENTIFIER"]))}},
                    col_links = {
                        "BOARD_NAME" : (lambda datum : url_for("board.board", board_id = datum["BOARD_ID"])),
                        "OPPONENT" : (lambda datum : url_for("user.user", username = datum["OPPONENT"]))
                        },
                    rows_per_view = 5,
                    col_types = {"TIME_LEFT_SECONDS" : "deadline"}
                    )
                sections_initialised += 1
            if active_games_not_your_turn_sample is not None:
                form_existing_games.add_ordered_table(sections_initialised, "active_games_not_your_turn",
                    f"""
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
                    ), rules AS (
                        SELECT GAME_ID, RULE AS deadline_rule
                        FROM BOC_RULESETS
                        WHERE RULE_GROUP = 'deadline'
                    )
                    SELECT
                        BOC_GAMES.GAME_ID AS GAME_ID,
                        CASE
                            WHEN BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])} THEN BOC_GAMES.PLAYER_B
                            ELSE BOC_GAMES.PLAYER_A
                        END AS OPPONENT,
                        BOC_GAMES.D_STARTED AS D_STARTED,
                        BOC_BOARDS.BOARD_ID AS BOARD_ID,
                        BOC_BOARDS.BOARD_NAME AS BOARD_NAME,
                        CASE
                            WHEN rules.deadline_rule = 'no_deadline'
                                THEN NULL
                            WHEN rules.deadline_rule = 'one_day_per_move'
                                THEN 86400 - COALESCE(
                                    strftime('%s','now') - strftime('%s',
                                        CASE WHEN BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])}
                                            THEN BOC_GAMES.PLAYER_A_PROMPTED
                                            ELSE BOC_GAMES.PLAYER_B_PROMPTED END
                                    ), 0
                                )
                            WHEN rules.deadline_rule = 'three_days_per_move'
                                THEN 259200 - COALESCE(
                                    strftime('%s','now') - strftime('%s',
                                        CASE WHEN BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])}
                                            THEN BOC_GAMES.PLAYER_A_PROMPTED
                                            ELSE BOC_GAMES.PLAYER_B_PROMPTED END
                                    ), 0
                                )
                            WHEN rules.deadline_rule = 'one_hour_cumulative'
                                THEN (CASE WHEN BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])}
                                        THEN BOC_GAMES.PLAYER_A_CUMULATIVE_SECONDS
                                        ELSE BOC_GAMES.PLAYER_B_CUMULATIVE_SECONDS END)
                                    - COALESCE(
                                        strftime('%s','now') - strftime('%s',
                                            CASE WHEN BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])}
                                                THEN BOC_GAMES.PLAYER_A_PROMPTED
                                                ELSE BOC_GAMES.PLAYER_B_PROMPTED END
                                        ), 0
                                    )
                            WHEN rules.deadline_rule = 'one_day_cumulative'
                                THEN (CASE WHEN BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])}
                                        THEN BOC_GAMES.PLAYER_A_CUMULATIVE_SECONDS
                                        ELSE BOC_GAMES.PLAYER_B_CUMULATIVE_SECONDS END)
                                    - COALESCE(
                                        strftime('%s','now') - strftime('%s',
                                            CASE WHEN BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])}
                                                THEN BOC_GAMES.PLAYER_A_PROMPTED
                                                ELSE BOC_GAMES.PLAYER_B_PROMPTED END
                                        ), 0
                                    )
                            ELSE NULL
                        END AS TIME_LEFT_SECONDS
                    FROM
                        BOC_GAMES JOIN latest_moves LM ON LM.GAME_ID = BOC_GAMES.GAME_ID
                        INNER JOIN BOC_BOARDS ON BOC_GAMES.BOARD_ID = BOC_BOARDS.BOARD_ID
                        JOIN rules ON rules.GAME_ID = BOC_GAMES.GAME_ID
                    WHERE
                        (BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])} OR BOC_GAMES.PLAYER_B = {json.dumps(g.user["username"])})
                        AND BOC_GAMES.STATUS = \"in_progress\"
                        AND (
                            (BOC_GAMES.PLAYER_A = {json.dumps(g.user["username"])} AND LM.players_at_latest = 'A')
                            OR
                            (BOC_GAMES.PLAYER_B = {json.dumps(g.user["username"])} AND LM.players_at_latest = 'B')
                        )
                    """, "GAME_ID", ["OPPONENT", "BOARD_NAME", "TIME_LEFT_SECONDS", "D_STARTED", "BOARD_ID"],
                    include_select = False,
                    headers = {"OPPONENT" : "Opponent", "BOARD_NAME" : "Board", "TIME_LEFT_SECONDS" : "Time left", "D_STARTED" : "Start date"},
                    order_options = [["D_STARTED", "Start"]],
                    actions = {"open" : "Open game"},
                    filters = False,
                    action_instructions = {"open" : {"type" : "link", "url_func" : (lambda datum : url_for("game_bp.game", game_id = datum["IDENTIFIER"]))}},
                    col_links = {
                        "BOARD_NAME" : (lambda datum : url_for("board.board", board_id = datum["BOARD_ID"])),
                        "OPPONENT" : (lambda datum : url_for("user.user", username = datum["OPPONENT"]))
                        },
                    rows_per_view = 5,
                    col_types = {"TIME_LEFT_SECONDS" : "deadline"}
                    )
            form_existing_games.realise_form()
            self.structured_html.append(form_existing_games.structured_html)

        self.close_container()
        self.close_container()

    def render_section_your_boards(self):
        db = get_db()
        # One action form with two tabs: Published boards and Workshop
        your_published_boards_sample = db.execute("SELECT BOARD_ID FROM BOC_BOARDS WHERE AUTHOR = ? AND IS_PUBLIC = 1 LIMIT 1", (g.user["username"],)).fetchone()
        any_published_boards = your_published_boards_sample is not None

        form_your_boards_tabs = ["Boards workshop"]
        if any_published_boards:
            form_your_boards_tabs.append("Public boards")

        form_your_boards = ActionForm("your_boards", "Your boards", "home")
        form_your_boards.initialise_tabs(form_your_boards_tabs)

        form_your_boards.add_ordered_table(0, "your_boards_unpublished",
            f"SELECT BOARD_ID, BOARD_NAME, D_CREATED, D_CHANGED FROM BOC_BOARDS WHERE BOC_BOARDS.AUTHOR = {json.dumps(g.user["username"])} AND BOC_BOARDS.IS_PUBLIC = 0",
            "BOARD_ID", ["BOARD_NAME", "D_CHANGED", "D_CREATED"],
            include_select = False,
            headers = {"BOARD_NAME" : "Board", "D_CHANGED" : "Changed", "D_CREATED" : "Created"},
            order_options = [["D_CHANGED", "Changed"]],
            actions = {"edit" : "Edit", "publish" : "Publish", "delete" : "Delete"},
            filters = ["BOARD_NAME"],
            action_instructions = {"edit" : {"type" : "link", "url_func" : (lambda datum : url_for("board.board", board_id = datum["IDENTIFIER"]))}},
            rows_per_view = 7
            )
        form_your_boards.add_button(0, "submit", "create_new_board", "Create new board", "create_new_board_btn")

        if any_published_boards:
            form_your_boards.add_ordered_table(1, "your_boards_published",
                f"""SELECT BOC_BOARDS.BOARD_ID as BOARD_ID, BOC_BOARDS.BOARD_NAME AS BOARD_NAME, BOC_BOARDS.D_PUBLISHED AS D_PUBLISHED, BOC_BOARDS.HANDICAP AS HANDICAP,
                        COUNT(BOC_GAMES.BOARD_ID) AS GAMES_PLAYED,
                        COUNT(BOC_USER_SAVED_BOARDS.BOARD_ID) AS SAVED_BY
                    FROM BOC_BOARDS
                        LEFT JOIN BOC_GAMES ON BOC_GAMES.BOARD_ID = BOC_BOARDS.BOARD_ID AND BOC_GAMES.STATUS = \"concluded\"
                        LEFT JOIN BOC_USER_SAVED_BOARDS ON BOC_USER_SAVED_BOARDS.BOARD_ID = BOC_BOARDS.BOARD_ID AND BOC_USER_SAVED_BOARDS.USERNAME != {json.dumps(g.user["username"])}
                    WHERE BOC_BOARDS.AUTHOR = {json.dumps(g.user["username"])} AND BOC_BOARDS.IS_PUBLIC = 1 GROUP BY BOC_BOARDS.BOARD_ID""",
                "BOARD_ID", ["BOARD_NAME", "D_PUBLISHED", "GAMES_PLAYED", "SAVED_BY", "HANDICAP"],
                include_select = False,
                headers = {"BOARD_NAME" : "Board", "D_PUBLISHED" : "Published", "GAMES_PLAYED" : "# games played", "SAVED_BY" : "# users saved", "HANDICAP" : "Handicap"},
                order_options = [["D_PUBLISHED", "Published"], ["GAMES_PLAYED", "# games"], ["SAVED_BY", "# users"]],
                actions = {"view" : "View", "fork" : "Fork", "hide" : "Hide"},
                filters = ["BOARD_NAME"],
                action_instructions = {"view" : {"type" : "link", "url_func" : (lambda datum : url_for("board.board", board_id = datum["IDENTIFIER"]))}},
                col_links = {
                    "BOARD_NAME" : (lambda datum : url_for("board.board", board_id = datum["IDENTIFIER"]))
                    },
                rows_per_view = 8
                )

        form_your_boards.realise_form()

        self.structured_html.append(form_your_boards.structured_html)


    def render_section_public_boards(self):
        # One action form with two tabs: Your collection and Marketplace
        form_public_boards = ActionForm("public_boards", "Public boards", "home")
        form_public_boards.initialise_tabs(["Board marketplace", "Saved boards"])
        form_public_boards.add_ordered_table(0, "board_marketplace_table",
            f"""SELECT BOC_BOARDS.BOARD_ID as BOARD_ID, BOC_BOARDS.BOARD_NAME AS BOARD_NAME, BOC_BOARDS.D_PUBLISHED AS D_PUBLISHED, BOC_BOARDS.HANDICAP AS HANDICAP, BOC_BOARDS.AUTHOR AS AUTHOR,
                    COUNT(BOC_GAMES.BOARD_ID) AS GAMES_PLAYED,
                    COUNT(BOC_USER_SAVED_BOARDS.BOARD_ID) AS SAVED_BY
            FROM BOC_BOARDS
                LEFT JOIN BOC_GAMES ON BOC_GAMES.BOARD_ID = BOC_BOARDS.BOARD_ID AND BOC_GAMES.STATUS = \"concluded\"
                LEFT JOIN BOC_USER_SAVED_BOARDS ON BOC_USER_SAVED_BOARDS.BOARD_ID = BOC_BOARDS.BOARD_ID AND BOC_USER_SAVED_BOARDS.USERNAME != {json.dumps(g.user["username"])}
            WHERE BOC_BOARDS.AUTHOR != {json.dumps(g.user["username"])} AND BOC_BOARDS.IS_PUBLIC = 1
            AND NOT EXISTS (
                SELECT 1 FROM BOC_USER_SAVED_BOARDS WHERE BOC_USER_SAVED_BOARDS.BOARD_ID = BOC_BOARDS.BOARD_ID AND BOC_USER_SAVED_BOARDS.USERNAME = {json.dumps(g.user["username"])})
            GROUP BY BOC_BOARDS.BOARD_ID""",
            "BOARD_ID", ["BOARD_NAME", "AUTHOR", "GAMES_PLAYED", "SAVED_BY", "D_PUBLISHED", "HANDICAP"], include_select = False,
            headers = {"BOARD_NAME" : "Board", "AUTHOR" : "Author", "GAMES_PLAYED" : "# games played", "SAVED_BY" : "# users saved", "D_PUBLISHED" : "Published", "HANDICAP" : "Handicap"},
            order_options = [["D_PUBLISHED", "Published"], ["GAMES_PLAYED", "# games"], ["SAVED_BY", "# users"], ["HANDICAP", "Handicap"]],
            actions = {"view" : "View", "save" : "Save"},
            filters = ["BOARD_NAME", "AUTHOR", "D_PUBLISHED"],
            action_instructions = {"view" : {"type" : "link", "url_func" : (lambda datum : url_for("board.board", board_id = datum["IDENTIFIER"]))}},
            col_links = {
                "BOARD_NAME" : (lambda datum : url_for("board.board", board_id = datum["IDENTIFIER"])),
                "AUTHOR" : (lambda datum : url_for("user.user", username = datum["AUTHOR"]))
                },
            rows_per_view = 8)
        form_public_boards.add_ordered_table(1, "your_saved_boards",
            f"""SELECT BOC_BOARDS.BOARD_ID as BOARD_ID, BOC_BOARDS.BOARD_NAME AS BOARD_NAME, BOC_BOARDS.D_PUBLISHED AS D_PUBLISHED, BOC_BOARDS.HANDICAP AS HANDICAP,
                    COUNT(BOC_GAMES.BOARD_ID) AS GAMES_PLAYED, BOC_BOARDS.AUTHOR AS AUTHOR, BOC_USER_SAVED_BOARDS.D_SAVED AS D_SAVED
                FROM BOC_BOARDS LEFT JOIN BOC_GAMES ON BOC_GAMES.BOARD_ID = BOC_BOARDS.BOARD_ID AND BOC_GAMES.STATUS = \"concluded\"
                                INNER JOIN BOC_USER_SAVED_BOARDS ON BOC_USER_SAVED_BOARDS.BOARD_ID = BOC_BOARDS.BOARD_ID AND BOC_USER_SAVED_BOARDS.USERNAME = {json.dumps(g.user["username"])}
            WHERE BOC_BOARDS.AUTHOR != {json.dumps(g.user["username"])} AND BOC_BOARDS.IS_PUBLIC = 1
            GROUP BY BOC_BOARDS.BOARD_ID""",
            "BOARD_ID", ["BOARD_NAME", "AUTHOR", "GAMES_PLAYED", "D_PUBLISHED", "D_SAVED", "HANDICAP"],
            include_select = False,
            headers = {"BOARD_NAME" : "Board", "AUTHOR" : "Author", "GAMES_PLAYED" : "# games played", "D_PUBLISHED" : "Published", "D_SAVED" : "Saved", "HANDICAP" : "Handicap"},
            order_options = [["D_SAVED", "Saved"], ["D_PUBLISHED", "Published"], ["GAMES_PLAYED", "# games"], ["HANDICAP", "Handicap"]],
            actions = {"view" : "View", "remove" : "Remove"},
            filters = ["BOARD_NAME", "AUTHOR", "D_PUBLISHED", "D_SAVED"],
            action_instructions = {"view" : {"type" : "link", "url_func" : (lambda datum : url_for("board.board", board_id = datum["IDENTIFIER"]))}},
            col_links = {
                "BOARD_NAME" : (lambda datum : url_for("board.board", board_id = datum["IDENTIFIER"])),
                "AUTHOR" : (lambda datum : url_for("user.user", username = datum["AUTHOR"]))
                },
            rows_per_view = 8)

        form_public_boards.realise_form()
        self.structured_html.append(form_public_boards.structured_html)

    def render_section_user_profiles(self):
        form_users = ActionForm("users", "Users", "home")
        form_users.initialise_tabs(["Leaderboard"])

        form_users.add_ordered_table(0, "leaderboard",
            f"""SELECT
            BOC_USER.USERNAME AS USERNAME, BOC_USER.RATING AS RATING, (SELECT COUNT(*) FROM BOC_GAMES WHERE ( ( (PLAYER_A = {json.dumps(g.user["username"])} AND PLAYER_B = BOC_USER.USERNAME) OR (PLAYER_B = {json.dumps(g.user["username"])} AND PLAYER_A = BOC_USER.USERNAME)) AND STATUS = \"concluded\")) AS COUNT_GAMES,
            CASE
                WHEN (EXISTS (SELECT 1
                    FROM BOC_USER_RELATIONSHIPS
                    WHERE (
                        (BOC_USER_RELATIONSHIPS.USER_1 = {json.dumps(g.user["username"])} AND BOC_USER_RELATIONSHIPS.USER_2 = BOC_USER.USERNAME)
                        OR
                        (BOC_USER_RELATIONSHIPS.USER_2 = {json.dumps(g.user["username"])} AND BOC_USER_RELATIONSHIPS.USER_1 = BOC_USER.USERNAME)
                    )
                    AND BOC_USER_RELATIONSHIPS.STATUS = "blocked")) OR BOC_USER.USERNAME = {json.dumps(g.user["username"])} THEN 0
                ELSE 1
            END AS IS_AMICABLE,
            CASE
                WHEN BOC_USER.USERNAME = {json.dumps(g.user["username"])} THEN 0
                ELSE 1
            END AS IS_NOT_YOU,
            CASE
                WHEN EXISTS (SELECT 1 FROM BOC_USER_RELATIONSHIPS
                    WHERE BOC_USER_RELATIONSHIPS.USER_1 = {json.dumps(g.user["username"])} AND BOC_USER_RELATIONSHIPS.USER_2 = BOC_USER.USERNAME AND BOC_USER_RELATIONSHIPS.STATUS = \"friends_pending\") THEN "withdraw_friend_request"
                WHEN EXISTS (SELECT 1 FROM BOC_USER_RELATIONSHIPS
                    WHERE BOC_USER_RELATIONSHIPS.USER_1 = BOC_USER.USERNAME AND BOC_USER_RELATIONSHIPS.USER_2 = {json.dumps(g.user["username"])} AND BOC_USER_RELATIONSHIPS.STATUS = \"friends_pending\") THEN "accept_friend_request"
                WHEN EXISTS (SELECT 1
                    FROM BOC_USER_RELATIONSHIPS
                    WHERE (
                        (BOC_USER_RELATIONSHIPS.USER_1 = {json.dumps(g.user["username"])} AND BOC_USER_RELATIONSHIPS.USER_2 = BOC_USER.USERNAME)
                        OR
                        (BOC_USER_RELATIONSHIPS.USER_2 = {json.dumps(g.user["username"])} AND BOC_USER_RELATIONSHIPS.USER_1 = BOC_USER.USERNAME)
                    )
                    AND BOC_USER_RELATIONSHIPS.STATUS = "friends") THEN \"unfriend\"
                ELSE "send_friend_request"
            END AS FRIEND_TOGGLE,
            CASE
                WHEN EXISTS (SELECT 1
                    FROM BOC_USER_RELATIONSHIPS
                    WHERE (BOC_USER_RELATIONSHIPS.USER_1 = {json.dumps(g.user["username"])} AND BOC_USER_RELATIONSHIPS.USER_2 = BOC_USER.USERNAME)
                        AND BOC_USER_RELATIONSHIPS.STATUS = "blocked") THEN \"unblock_user\"
                ELSE \"block_user\"
            END AS BLOCK_TOGGLE
            FROM BOC_USER""",
            "USERNAME", ["USERNAME", "RATING", "COUNT_GAMES", "IS_AMICABLE", "IS_NOT_YOU", "FRIEND_TOGGLE", "BLOCK_TOGGLE"],
            include_select = False,
            headers = {"USERNAME" : "User", "RATING" : "Rating", "COUNT_GAMES" : "# of games played with you"},
            order_options = [["RATING", "Rating"], ["COUNT_GAMES", "# games"], ["USERNAME", "Username"]],
            actions = {"view" : "View", "send_friend_request" : "Befriend", "accept_friend_request" : "Accept", "withdraw_friend_request" : "Withdraw", "unfriend" : "Unfriend", "block_user" : "Block", "unblock_user" : "Unblock"},
            filters = ["USERNAME", "RATING", "COUNT_GAMES"],
            action_instructions = {
                "view" : {"type" : "link", "url_func" : (lambda datum : url_for("user.user", username = datum["IDENTIFIER"]))},
                "send_friend_request" : {"condition" : "IS_AMICABLE", "toggle" : "FRIEND_TOGGLE"},
                "accept_friend_request" : {"toggle" : "FRIEND_TOGGLE"},
                "withdraw_friend_request" : {"toggle" : "FRIEND_TOGGLE"},
                "unfriend" : {"toggle" : "FRIEND_TOGGLE"},
                "block_user" : {"condition" : "IS_NOT_YOU", "toggle" : "BLOCK_TOGGLE"},
                "unblock_user" : {"toggle" : "BLOCK_TOGGLE"}
                },
            col_links = {
                "USERNAME" : (lambda datum : url_for("user.user", username = datum["IDENTIFIER"]))
                },
            rows_per_view = 8,
            enforce_filter_kw = "WHERE",
            row_class_by_col = "IS_NOT_YOU")

        form_users.realise_form()
        self.structured_html.append(form_users.structured_html)


    def render_section_your_profile(self):
        db = get_db()
        # If you have any pending friend requests sent your way, they will be displayed in a separate form on top
        self.open_container("your_profile_forms_container")

        pending_friend_requests_sample = db.execute("SELECT * FROM BOC_USER_RELATIONSHIPS WHERE USER_2 = ? AND STATUS = \"friends_pending\" LIMIT 1", (g.user["username"],)).fetchone()
        if pending_friend_requests_sample is not None:
            form_pending_friend_requests = ActionForm("pending_friend_requests", "Pending friend requests", "home")
            form_pending_friend_requests.initialise_tabs(["Friend requests for you"])
            form_pending_friend_requests.add_ordered_table(0, "friend_requests_for_you",
                f"SELECT USER_1, D_STATUS FROM BOC_USER_RELATIONSHIPS WHERE USER_2 = {json.dumps(g.user["username"])} AND STATUS = \"friends_pending\"",
                "USER_1", ["USER_1", "D_STATUS"],
                include_select = False,
                headers = {"USER_1" : "Sender", "D_STATUS" : "When received"},
                order_options = [["D_STATUS", "Received"]],
                actions = {"accept" : "Accept", "view" : "View", "decline" : "Decline"},
                filters = ["USER_1", "D_STATUS"],
                action_instructions = {"view" : {"type" : "link", "url_func" : (lambda datum : url_for("user.user", username = datum["IDENTIFIER"]))}},
                col_links = {
                    "USER_1" : (lambda datum : url_for("user.user", username = datum["IDENTIFIER"]))
                    },
                rows_per_view = 3)

            form_pending_friend_requests.realise_form()
            self.structured_html.append(form_pending_friend_requests.structured_html)

        form_your_profile = ActionForm("your_profile", "Profile", "home", allow_file_encoding = True)
        form_your_profile.initialise_tabs(["Personal settings", "Archive", "Friends", "Blocked"])
        # Personal settings: change pfp, change password, set language etc
        personal_settings_form = [
            f"  <h2>Profile picture</h2>",
            f"  <label for=\"new_profile_picture\">Upload profile picture:</label>",
            f"  <input type=\"file\" id=\"new_profile_picture\" name=\"new_profile_picture\" accept=\"image/*\">",
            f"  <h2>Language</h2>",
            f"  <label for=\"user_language_select\">Select language:</label>",
            f"  <select name=\"user_language_select\" id=\"user_language_select\">",
            f"    <option value=\"english\">English</option>",
            f"    <option value=\"french\">French</option>",
            f"    <option value=\"czech\">Raz som si tak nadrbal palec na nohe až mi guľky zmakoveli</option>",
            f"    <option value=\"slovak\">Slovak</option>",
            f"  </select>",
            f"  <h2>Change password</h2>",
            f"  <label for=\"new_password\">New password</label>",
            f"  <input type=\"password\" name=\"new_password\" id=\"new_password\">",
            f"  <label for=\"new_password_confirm\">Confirm password</label>",
            f"  <input type=\"password\" name=\"new_password_confirm\" id=\"new_password_confirm\">",
            ]
        form_your_profile.add_to_tab(0, "content", personal_settings_form)
        form_your_profile.add_button(0, "submit", "save_changes", "Save changes", "save_changes")

        # Archive of past games
        form_your_profile.add_game_archive(1, "your_archive", g.user["username"], rows_per_view = 8)

        # List of friends
        form_your_profile.add_ordered_table(2, "your_friends",
            f"""SELECT BOC_USER.USERNAME AS USERNAME, BOC_USER.RATING AS RATING, (SELECT COUNT(*) FROM BOC_GAMES WHERE ( ( (PLAYER_A = {json.dumps(g.user["username"])} AND PLAYER_B = BOC_USER.USERNAME) OR (PLAYER_B = {json.dumps(g.user["username"])} AND PLAYER_A = BOC_USER.USERNAME)) AND STATUS = \"concluded\")) AS COUNT_GAMES FROM BOC_USER INNER JOIN BOC_USER_RELATIONSHIPS ON ((BOC_USER.USERNAME = BOC_USER_RELATIONSHIPS.USER_1 AND BOC_USER_RELATIONSHIPS.USER_2 = {json.dumps(g.user["username"])}) OR (BOC_USER.USERNAME = BOC_USER_RELATIONSHIPS.USER_2 AND BOC_USER_RELATIONSHIPS.USER_1 = {json.dumps(g.user["username"])})) AND BOC_USER_RELATIONSHIPS.STATUS=\"friends\"""",
            "USERNAME", ["USERNAME", "RATING", "COUNT_GAMES"],
            include_select = False,
            headers = {"USERNAME" : "User", "RATING" : "Rating", "COUNT_GAMES" : "# of games played with you"},
            order_options = [["COUNT_GAMES", "# games"], ["RATING", "Rating"], ["USERNAME", "Username"]],
            actions = {"view" : "View", "unfriend" : "Unfriend"},
            filters = ["USERNAME", "RATING", "COUNT_GAMES"],
            action_instructions = {"view" : {"type" : "link", "url_func" : (lambda datum : url_for("user.user", username = datum["IDENTIFIER"]))}},
            col_links = {
                "USERNAME" : (lambda datum : url_for("user.user", username = datum["IDENTIFIER"]))
                },
            rows_per_view = 8,
            enforce_filter_kw = "WHERE")

        # List of blocked users
        form_your_profile.add_ordered_table(3, "your_blocked",
            f"""SELECT BOC_USER.USERNAME AS USERNAME, BOC_USER.RATING AS RATING, (SELECT COUNT(*) FROM BOC_GAMES WHERE ( ( (PLAYER_A = {json.dumps(g.user["username"])} AND PLAYER_B = BOC_USER.USERNAME) OR (PLAYER_B = {json.dumps(g.user["username"])} AND PLAYER_A = BOC_USER.USERNAME)) AND STATUS = \"concluded\")) AS COUNT_GAMES FROM BOC_USER INNER JOIN BOC_USER_RELATIONSHIPS ON (BOC_USER.USERNAME = BOC_USER_RELATIONSHIPS.USER_2 AND BOC_USER_RELATIONSHIPS.USER_1 = {json.dumps(g.user["username"])}) AND BOC_USER_RELATIONSHIPS.STATUS=\"blocked\"""",
            "USERNAME", ["USERNAME", "RATING", "COUNT_GAMES"],
            include_select = False,
            headers = {"USERNAME" : "User", "RATING" : "Rating", "COUNT_GAMES" : "# of games played with you"},
            order_options = [["COUNT_GAMES", "# games"], ["RATING", "Rating"], ["USERNAME", "Username"]],
            actions = {"view" : "View", "unblock" : "Unblock"},
            filters = ["USERNAME", "RATING", "COUNT_GAMES"],
            action_instructions = {"view" : {"type" : "link", "url_func" : (lambda datum : url_for("user.user", username = datum["IDENTIFIER"]))}},
            col_links = {
                "USERNAME" : (lambda datum : url_for("user.user", username = datum["IDENTIFIER"]))
                },
            rows_per_view = 8,
            enforce_filter_kw = "WHERE")

        form_your_profile.realise_form()
        self.structured_html.append(form_your_profile.structured_html)

        self.close_container()

    def render_section_tutorials(self):
        if g.user:
            db = get_db()
            client_privilege = db.execute("SELECT PRIVILEGE FROM BOC_USER WHERE USERNAME = ?", (g.user["username"],)).fetchone()["PRIVILEGE"]
        else:
            client_privilege = "GUEST"

        tutorial_guide = TreeDocumentViewer("tutorial_guide", "home", "index", client_privilege, {"section" : 5})

        self.structured_html.append(tutorial_guide.structured_html)




    def render_content_logged_in(self):
        self.initialise_sections({"play" : "Play", "your_boards" : "Your boards", "public_boards" : "Public boards", "user_profiles" : "Users", "your_profile_section" : "Profile", "tutorials_section" : "Tutorial"})
        self.render_section_play()
        self.open_next_section()
        self.render_section_your_boards()
        self.open_next_section()
        self.render_section_public_boards()
        self.open_next_section()
        self.render_section_user_profiles()
        self.open_next_section()
        self.render_section_your_profile()
        self.open_next_section()
        self.render_section_tutorials()
        self.close_sections()



    def render_page(self):
        self.resolve_request()
        self.html_open("style")
        self.html_navbar()

        # Check if logged in
        if g.user:
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
