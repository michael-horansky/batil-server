import json
from datetime import datetime, timezone

from batil.html_objects.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.db import get_db, get_table_as_list_of_dicts, conclude_and_rate_game

from batil.engine.game_logic.class_Gamemaster import Gamemaster
from batil.engine.rendering.class_HTMLRenderer import HTMLRenderer
from batil.engine.rendering.class_Abstract_Output import Abstract_Output


class PageTutorial(Page):

    def __init__(self, tutorial_id):
        super().__init__("Tutorial")
        self.tutorial_id = tutorial_id
        self.client_role = None

        self.gm = Gamemaster(display_logs = False)

        # We determine the role
        db = get_db()
        self.tutorial_row = db.execute("""
            SELECT
                BOC_TUTORIALS.TUTORIAL_ID AS TUTORIAL_ID,
                BOC_TUTORIALS.AUTHOR AS AUTHOR,
                BOC_TUTORIALS.BOARD_ID AS BOARD_ID,
                BOC_TUTORIALS.STATUS AS STATUS,
                BOC_TUTORIALS.OUTCOME AS OUTCOME,
                BOC_TUTORIALS.D_CREATED AS D_CREATED,
                BOC_TUTORIALS.D_CHANGED AS D_CHANGED,
                BOC_BOARDS.BOARD_NAME AS BOARD_NAME
            FROM BOC_TUTORIALS INNER JOIN BOC_BOARDS ON BOC_TUTORIALS.BOARD_ID = BOC_BOARDS.BOARD_ID WHERE TUTORIAL_ID = ?
            """, (self.tutorial_id,)).fetchone()
        if self.tutorial_row is None:
            print(f"ERROR: Attempting to load a non-existing game (game-id = {self.game_id})")
            return(-1)
        self.game_status = self.tutorial_row["STATUS"]
        self.game_outcome = self.tutorial_row["OUTCOME"]

        # We now identify the user who opened the page
        self.link_data = {
            "board" : self.tutorial_row["BOARD_ID"],
            "board_name" : self.tutorial_row["BOARD_NAME"]
            }
        if g.user is not None:
            if self.tutorial_row["AUTHOR"] == g.user["username"]:
                self.client_role = "editor"
            else:
                self.client_role = "guest"

    def resolve_request(self):
        db = get_db()
        print("Resolving POST...")
        if request.method == 'POST':
            # We check what action is happening
            for key, val in request.form.items():
                print(f"{key} -> {val}")


    def resolve_tutorial_edit_submission(self):
        db = get_db()
        return(0)
        # Before we even consider looking at the moves, we check if the game didn't end by timeout.
        """time_control_rule = db.execute("SELECT RULE FROM BOC_RULESETS WHERE GAME_ID = ? AND RULE_GROUP = \"deadline\"", (self.game_id,)).fetchone()["RULE"]

        if time_control_rule != "no_deadline":
            # We note current time
            current_time = datetime.utcnow()
            self.check_for_timeout(time_control_rule, current_time, self.client_role)
            if self.game_status == "in_progress":
                # The player managed to submit commands without timing out.
                # self.time_countdown is now guaranteed to store the time left.
                # it is type int and is in total seconds.
                if time_control_rule in ["one_hour_cumulative", "one_day_cumulative"]:
                    db.execute(f"UPDATE BOC_GAMES SET PLAYER_{self.client_role}_CUMULATIVE_SECONDS = ? WHERE GAME_ID = ?", (self.time_countdown, self.game_id))
        db.execute(f"UPDATE BOC_GAMES SET PLAYER_{self.client_role}_PROMPTED = NULL WHERE GAME_ID = ?", (self.game_id,))

        stones_touched_in_order = [int(x) for x in request.form.get("touch_order").split(",")]
        commands_added = []
        for stone_ID in stones_touched_in_order:
            cur_cmd = {}
            for default_keyword in Abstract_Output.command_keywords:
                if default_keyword in Abstract_Output.integer_command_keywords:
                    if request.form.get(f"cmd_{default_keyword}_{stone_ID}") != "":
                        cur_cmd[default_keyword] = int(request.form.get(f"cmd_{default_keyword}_{stone_ID}"))
                    else:
                        cur_cmd[default_keyword] = None
                else:
                    cur_cmd[default_keyword] = request.form.get(f"cmd_{default_keyword}_{stone_ID}")
            commands_added.append(cur_cmd)
        output_message = self.gm.submit_commands(self.client_role, commands_added)
        if output_message.header == "error":
            db.execute("INSERT INTO BOC_SYSTEM_LOGS (PRIORITY, ORIGIN, MESSAGE) VALUES (4, \"page_game.resolve_command_submission\", ?)", output_message.msg)
            db.commit()
            return(-1)
        new_dynamic_rep = self.gm.dump_changes()
        # We save changes to database
        for turn_index in range(len(new_dynamic_rep)):
            for commander, command_rep in new_dynamic_rep[turn_index].items():
                db.execute("INSERT INTO BOC_MOVES (GAME_ID, TURN_INDEX, PLAYER, REPRESENTATION, D_MOVE) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)", (self.game_id, turn_index, commander, command_rep))

        if output_message.header == "concluded":
            conclude_and_rate_game(self.game_id, output_message.msg)
            self.game_status = "concluded"

        db.commit()"""

    def load_game(self):
        db = get_db()
        # We need to load the static data, the dynamic data, and the ruleset
        static_data_row = db.execute("SELECT T_DIM, X_DIM, Y_DIM, STATIC_REPRESENTATION FROM BOC_BOARDS WHERE BOARD_ID = ?", (self.game_row["BOARD_ID"],)).fetchone()
        static_data = {
                "t_dim" : static_data_row["T_DIM"],
                "x_dim" : static_data_row["X_DIM"],
                "y_dim" : static_data_row["Y_DIM"],
                "board_static" : static_data_row["STATIC_REPRESENTATION"]
            }

        dynamic_data_rows = db.execute("SELECT TURN_INDEX, PLAYER, REPRESENTATION FROM BOC_TUTORIAL_MOVES WHERE TUTORIAL_ID = ?", (self.tutorial_id,)).fetchall()
        max_turn_index = 0
        for row in dynamic_data_rows:
            if row["TURN_INDEX"] > max_turn_index:
                max_turn_index = row["TURN_INDEX"]

        dynamic_data = []
        for i in range(max_turn_index + 1):
            dynamic_data.append({})

        for row in dynamic_data_rows:
            dynamic_data[row["TURN_INDEX"]][row["PLAYER"]] = row["REPRESENTATION"]

        ruleset_rows = db.execute("SELECT RULE_GROUP, RULE FROM BOC_TUTORIAL_RULESETS WHERE TUTORIAL_ID = ?", (self.game_id,)).fetchall()
        ruleset = {}
        for row in ruleset_rows:
            ruleset[row["RULE_GROUP"]] = row["RULE"]

        if self.game_status == "in_progress":
            self.gm.load_from_database(static_data, dynamic_data, ruleset)
        else:
            self.gm.load_from_database(static_data, dynamic_data, ruleset, self.game_outcome)




    def prepare_renderer(self):
        # Time for telling the proprietary gamemaster to properly initialise the game with the correct access rights
        return(0)
        # TODO special renderer for tutorials ofc! also client role for editors can be set manually between A and B
        #self.gm.prepare_for_rendering(self.client_role)
        #self.renderer = HTMLRenderer(self.gm.rendering_output, self.game_id, self.client_role, self.game_management_status)
        #self.renderer.render_game(self.link_data)


    def render_page(self):
        # First we load the game from database
        #self.load_game()
        # Then we check the POST form to see if new commands were submitted. If yes, we incorporate them into the render object, and also upload them to the db
        #self.resolve_request()
        # Finally, we prepare the rendering object
        self.prepare_renderer()

        self.html_open("boc_tutorial")

        """self.structured_html.append(self.renderer.structured_output)

        if self.game_status == "in_progress":
            if self.gm.rendering_output.did_player_finish_turn:
                # The client is waiting for his opponent; we will check the page automatically once the game has been updated
                self.clientside_reloader(waiting_for_move = True)
            else:
                self.clientside_reloader(waiting_for_move = False)

        self.structured_html.append("</body>")"""

        return(self.print_html())

