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


class PageGame(Page):

    def __init__(self, game_id):
        super().__init__("Game")
        self.game_id = game_id
        self.game_status = None
        self.game_management_status = None
        self.client_role = None

        self.time_countdown = None

        self.gm = Gamemaster(display_logs = True)

        # We determine the role
        db = get_db()
        self.game_row = db.execute("""
            SELECT
                BOC_GAMES.PLAYER_A AS PLAYER_A,
                BOC_GAMES.PLAYER_B AS PLAYER_B,
                BOC_GAMES.BOARD_ID AS BOARD_ID,
                BOC_GAMES.STATUS AS STATUS,
                BOC_GAMES.DRAW_OFFER_STATUS AS DRAW_OFFER_STATUS,
                BOC_GAMES.OUTCOME AS OUTCOME,
                BOC_GAMES.PLAYER_A_PROMPTED AS PLAYER_A_PROMPTED,
                BOC_GAMES.PLAYER_B_PROMPTED AS PLAYER_B_PROMPTED,
                BOC_GAMES.PLAYER_A_DEADLINE AS PLAYER_A_DEADLINE,
                BOC_GAMES.PLAYER_B_DEADLINE AS PLAYER_B_DEADLINE,
                BOC_GAMES.PLAYER_A_CUMULATIVE_SECONDS AS PLAYER_A_CUMULATIVE_SECONDS,
                BOC_GAMES.PLAYER_B_CUMULATIVE_SECONDS AS PLAYER_B_CUMULATIVE_SECONDS,
                BOC_BOARDS.BOARD_NAME AS BOARD_NAME
            FROM BOC_GAMES INNER JOIN BOC_BOARDS ON BOC_GAMES.BOARD_ID = BOC_BOARDS.BOARD_ID WHERE GAME_ID = ?
            """, (self.game_id,)).fetchone()
        print("------------------------------")
        for key in ["PLAYER_A_PROMPTED", "PLAYER_B_PROMPTED", "PLAYER_A_DEADLINE", "PLAYER_B_DEADLINE", "PLAYER_A_CUMULATIVE_SECONDS", "PLAYER_B_CUMULATIVE_SECONDS"]:
            print(f"  {key} -> {self.game_row[key]}")
        print("------------------------------")
        self.game_status = self.game_row["STATUS"]
        self.game_outcome = self.game_row["OUTCOME"]
        if self.game_row is None:
            print(f"ERROR: Attempting to load a non-existing game (game-id = {self.game_id})")
            return(-1)

        # We now identify the user who opened the page
        self.link_data = {
            "A" : self.game_row["PLAYER_A"],
            "B" : self.game_row["PLAYER_B"],
            "board" : self.game_row["BOARD_ID"],
            "board_name" : self.game_row["BOARD_NAME"]
            }
        if g.user is not None:
            if self.game_row["STATUS"] == "in_progress":
                if g.user["username"] == self.game_row["PLAYER_A"]:
                    self.client_role = "A"
                elif g.user["username"] == self.game_row["PLAYER_B"]:
                    self.client_role = "B"
                else:
                    self.client_role = "guest"
            else:
                self.client_role = "guest"

        self.game_management_status = {
            "DRAW_OFFER_STATUS" : self.game_row["DRAW_OFFER_STATUS"]
            }

    def resolve_request(self):
        db = get_db()
        print("Resolving POST...")
        if request.method == 'POST':
            # We check what action is happening
            pass


    def resolve_command_submission(self):
        db = get_db()
        # Before we even consider looking at the moves, we check if the game didn't end by timeout.
        time_control_rule = db.execute("SELECT RULE FROM BOC_RULESETS WHERE GAME_ID = ? AND RULE_GROUP = \"deadline\"", (self.game_id,)).fetchone()["RULE"]

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
            print(output_message.msg)
            return(-1)
        new_dynamic_rep = self.gm.dump_changes()
        # We save changes to database
        print("The following new commands will be saved:")
        for turn_index in range(len(new_dynamic_rep)):
            for commander, command_rep in new_dynamic_rep[turn_index].items():
                print(f"{turn_index} [{commander}]: {command_rep}")
                db.execute("INSERT INTO BOC_MOVES (GAME_ID, TURN_INDEX, PLAYER, REPRESENTATION, D_MOVE) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)", (self.game_id, turn_index, commander, command_rep))

        if output_message.header == "concluded":
            conclude_and_rate_game(self.game_id, output_message.msg)
            self.game_status = "concluded"

        db.commit()

    def resolve_action_game_management(self):
        db = get_db()
        for key, val in request.form.items():
            print(f"{key} -> {val}")
        active_client = request.form.get("client_role")
        if active_client == "A":
            opposite_client = "B"
        else:
            opposite_client = "A"
        if request.form.get("action_game_management") == "offer_draw":
            game_draw_status = db.execute("SELECT DRAW_OFFER_STATUS FROM BOC_GAMES WHERE GAME_ID = ?", (self.game_id,)).fetchone()["DRAW_OFFER_STATUS"]
            if (active_client == "A" and game_draw_status == "B_offer") or (active_client == "B" and game_draw_status == "A_offer"):
                # draw accepted
                conclude_and_rate_game(self.game_id, "draw", "accepted", f"{opposite_client}_offer")
                db.commit()
            elif game_draw_status == "no_offer":
                db.execute(f"UPDATE BOC_GAMES SET DRAW_OFFER_STATUS = \"{active_client}_offer\" WHERE GAME_ID = ?", (self.game_id,))
                db.commit()
        elif request.form.get("action_game_management") == "withdraw_draw_offer":
            db.execute(f"UPDATE BOC_GAMES SET DRAW_OFFER_STATUS = \"no_offer\" WHERE GAME_ID = ? AND DRAW_OFFER_STATUS = \"{active_client}_offer\"", (self.game_id,))
            db.commit()
        elif request.form.get("action_game_management") == "decline_draw_offer":
            db.execute(f"UPDATE BOC_GAMES SET DRAW_OFFER_STATUS = \"no_offer\" WHERE GAME_ID = ? AND DRAW_OFFER_STATUS = \"{opposite_client}_offer\"", (self.game_id,))
            db.commit()
        elif request.form.get("action_game_management") == "accept_draw_offer":
            conclude_and_rate_game(self.game_id, "draw", "accepted", f"{opposite_client}_offer")
            db.commit()

        elif request.form.get("action_game_management") == "resign":
            conclude_and_rate_game(self.game_id, opposite_client)
            db.commit()

    def resolve_time_control(self):
        db = get_db()


        # First, we grab the particular time control ruleset
        time_control_rule = db.execute("SELECT RULE FROM BOC_RULESETS WHERE GAME_ID = ? AND RULE_GROUP = \"deadline\"", (self.game_id,)).fetchone()["RULE"]
        if time_control_rule == "no_deadline":
            # We skip this method
            return(None)

        # We note current time
        current_time = datetime.utcnow()

        # Is there a prompt time associated with this player?
        if self.game_row[f"PLAYER_{self.client_role}_PROMPTED"] is not None:
            self.check_for_timeout(time_control_rule, current_time, self.client_role)
        else:
            # The player has not been prompted. We now check if they just were
            # prompted, and register the potential prompt and deadline times.
            is_client_prompted = db.execute("""
                WITH latest AS (
                    SELECT MAX(BOC_MOVES.TURN_INDEX) AS max_turn
                    FROM BOC_MOVES
                    WHERE GAME_ID = :game_id
                ),
                latest_moves AS (
                    SELECT GROUP_CONCAT(PLAYER) AS players_at_latest
                    FROM BOC_MOVES, latest
                    WHERE BOC_MOVES.GAME_ID = :game_id
                    AND BOC_MOVES.TURN_INDEX = latest.max_turn
                )
                SELECT
                    CASE
                        WHEN (
                            (:client_role = 'A' AND players_at_latest = 'A')
                            OR
                            (:client_role = 'B' AND players_at_latest = 'B')
                        )
                        THEN 0
                        ELSE 1
                    END AS IS_THEIR_TURN
                FROM latest_moves;""", {"game_id" : self.game_id, "client_role" : self.client_role}).fetchone()["IS_THEIR_TURN"] == 1
            if is_client_prompted:
                # We save the time of the prompting, and the corresponding deadline if it exists
                if time_control_rule in ["one_day_per_move", "three_days_per_move"]:
                    if time_control_rule == "one_day_per_move":
                        db.execute(f"UPDATE BOC_GAMES SET PLAYER_{self.client_role}_PROMPTED = CURRENT_TIMESTAMP, PLAYER_{self.client_role}_DEADLINE = DATETIME(CURRENT_TIMESTAMP, '+1 day') WHERE GAME_ID = ?", (self.game_id,))
                        db.commit()
                        self.time_countdown = 3600 * 24
                    elif time_control_rule == "three_days_per_move":
                        db.execute(f"UPDATE BOC_GAMES SET PLAYER_{self.client_role}_PROMPTED = CURRENT_TIMESTAMP, PLAYER_{self.client_role}_DEADLINE = DATETIME(CURRENT_TIMESTAMP, '+3 days') WHERE GAME_ID = ?", (self.game_id,))
                        db.commit()
                        self.time_countdown = 3600 * 24 * 3
                elif time_control_rule in ["one_hour_cumulative", "one_day_cumulative"]:
                    db.execute(f"UPDATE BOC_GAMES SET PLAYER_{self.client_role}_PROMPTED = CURRENT_TIMESTAMP WHERE GAME_ID = ?", (self.game_id,))
                    db.commit()
                    self.time_countdown = int(self.game_row[f"PLAYER_{self.client_role}_CUMULATIVE_SECONDS"])
            else:
                # client is not prompted. We want to freeze the timer
                if time_control_rule in ["one_day_per_move", "three_days_per_move"]:
                    if time_control_rule == "one_day_per_move":
                        self.time_countdown = 3600 * 24
                    elif time_control_rule == "three_days_per_move":
                        self.time_countdown = 3600 * 24 * 3
                elif time_control_rule in ["one_hour_cumulative", "one_day_cumulative"]:
                    self.time_countdown = int(self.game_row[f"PLAYER_{self.client_role}_CUMULATIVE_SECONDS"])

    def check_for_timeout(self, time_control_rule, current_time, client_role):
        # For when the player has been prompted before,
        # and they either open the client or submit commands.
        # We now check for game end by timeout
        db = get_db()

        if client_role == "A":
            opposite_client = "B"
        else:
            opposite_client = "A"

        client_timeout = False
        opponent_timeout = False

        d_prompted = self.game_row[f"PLAYER_{client_role}_PROMPTED"]
        d_deadline = self.game_row[f"PLAYER_{client_role}_DEADLINE"]
        d_cumulative = self.game_row[f"PLAYER_{client_role}_CUMULATIVE_SECONDS"]
        d_prompted_opp = self.game_row[f"PLAYER_{opposite_client}_PROMPTED"]
        d_deadline_opp = self.game_row[f"PLAYER_{opposite_client}_DEADLINE"]
        d_cumulative_opp = self.game_row[f"PLAYER_{opposite_client}_CUMULATIVE_SECONDS"]
        if time_control_rule in ["one_day_per_move", "three_days_per_move"]:
            # We simply check if current time is bigger than the set
            # deadline. The particular deadline setting occurs elsewhere.

            if d_prompted is not None:
                d_deadline_value = datetime.fromisoformat(d_deadline)
                if current_time > d_deadline_value:
                    client_timeout = True
                else:
                    # We note how much time is left for the renderer
                    self.time_countdown = int((d_deadline_value - current_time).total_seconds())
            if d_prompted_opp is not None:
                d_deadline_opp_value = datetime.fromisoformat(d_deadline_opp)
                if current_time > d_deadline_opp_value:
                    opponent_timeout = True


        elif time_control_rule in ["one_hour_cumulative", "one_day_cumulative"]:
            # cumulative

            # This player has already been prompted. We load the time that
            # elapsed since the time at which they were prompted. Note that
            # this interval is NOT yet applied to the cumulative sum!

            if d_prompted is not None:
                d_prompted_value = datetime.fromisoformat(d_prompted)
                d_cumulative_value = int(d_cumulative)
                time_elapsed_since_prompted = (current_time - d_prompted_value).total_seconds()
                time_left = d_cumulative_value - time_elapsed_since_prompted

                if time_left < 0:
                    client_timeout = True
                else:
                    # We note how much time is left for the renderer
                    self.time_countdown = int(time_left)
            if d_prompted_opp is not None:
                d_prompted_opp_value = datetime.fromisoformat(d_prompted_opp)
                d_cumulative_opp_value = int(d_cumulative_opp)
                time_elapsed_since_prompted_opp = (current_time - d_prompted_opp_value).total_seconds()
                time_left_opp = d_cumulative_opp_value - time_elapsed_since_prompted_opp
                if time_left_opp < 0:
                    opponent_timeout = True


        if client_timeout:
            if opponent_timeout:
                # draw
                self.game_status = "concluded"
                self.game_outcome = "draw"
                conclude_and_rate_game(self.game_id, self.game_outcome)
                db.commit()
            else:
                # opponent won
                self.game_status = "concluded"
                self.game_outcome = opposite_client
                conclude_and_rate_game(self.game_id, self.game_outcome)
                db.commit()
        else:
            if opponent_timeout:
                # client won
                self.game_status = "concluded"
                self.game_outcome = client_role
                conclude_and_rate_game(self.game_id, self.game_outcome)
                db.commit()

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

        dynamic_data_rows = db.execute("SELECT TURN_INDEX, PLAYER, REPRESENTATION FROM BOC_MOVES WHERE GAME_ID = ?", (self.game_id,)).fetchall()
        max_turn_index = 0
        for row in dynamic_data_rows:
            if row["TURN_INDEX"] > max_turn_index:
                max_turn_index = row["TURN_INDEX"]

        dynamic_data = []
        for i in range(max_turn_index + 1):
            dynamic_data.append({})

        for row in dynamic_data_rows:
            dynamic_data[row["TURN_INDEX"]][row["PLAYER"]] = row["REPRESENTATION"]

        ruleset_rows = db.execute("SELECT RULE_GROUP, RULE FROM BOC_RULESETS WHERE GAME_ID = ?", (self.game_id,)).fetchall()
        ruleset = {}
        for row in ruleset_rows:
            ruleset[row["RULE_GROUP"]] = row["RULE"]

        if self.game_status == "in_progress":
            self.gm.load_from_database(static_data, dynamic_data, ruleset)
        else:
            self.gm.load_from_database(static_data, dynamic_data, ruleset, self.game_outcome)




    def prepare_renderer(self):
        # Time for telling the proprietary gamemaster to properly initialise the game with the correct access rights
        self.gm.prepare_for_rendering(self.client_role)
        self.renderer = HTMLRenderer(self.gm.rendering_output, self.game_id, self.client_role, self.game_management_status)
        self.renderer.render_game(self.link_data, self.time_countdown)


    def render_page(self):
        # First we load the game from database
        #self.load_game()
        # Then we check the POST form to see if new commands were submitted. If yes, we incorporate them into the render object, and also upload them to the db
        #self.resolve_request()
        # Finally, we prepare the rendering object
        self.prepare_renderer()

        self.html_open("boc_ingame")

        self.structured_html.append(self.renderer.structured_output)

        if self.game_status == "in_progress":
            if self.gm.rendering_output.did_player_finish_turn:
                # The client is waiting for his opponent; we will check the page automatically once the game has been updated
                self.clientside_reloader(waiting_for_move = True)
            else:
                self.clientside_reloader(waiting_for_move = False)

        self.structured_html.append("</body>")

        return(self.print_html())


    def clientside_reloader(self, waiting_for_move):
        # Prepares a JS daemon which checks whether to reload the game
        draw_offer_status = self.game_management_status["DRAW_OFFER_STATUS"]
        if waiting_for_move:
            db = get_db()
            initial_move_count = db.execute("SELECT COUNT(*) AS MOVES_COUNT FROM BOC_MOVES WHERE GAME_ID = ?", (self.game_id,)).fetchone()["MOVES_COUNT"]
            self.structured_html.append(f"""
                <script>
                let draw_offer_status = \"{draw_offer_status}\";
                let move_count = {initial_move_count};
                let move_count_url = \"{url_for("game_bp.moves_count", game_id=self.game_id)}\";

                async function poll_moves() {{
                    const resp = await fetch(`${{move_count_url}}?dos=${{draw_offer_status}}&count=${{move_count}}`);
                    const data = await resp.json();

                    if (data.changed) {{
                        move_count = data.count;
                        window.location.href = window.location.pathname + \"?last_displayed_turn=\" + encodeURIComponent({self.gm.rendering_output.current_turn});
                    }}

                    setTimeout(poll_moves, 1000);
                }}

                poll_moves();
                </script>
            """)
        else:
            self.structured_html.append(f"""
                <script>
                let draw_offer_status = \"{draw_offer_status}\";
                let game_status_url = \"{url_for("game_bp.game_status", game_id=self.game_id)}\";

                async function poll_moves() {{
                    const resp = await fetch(`${{game_status_url}}?dos=${{draw_offer_status}}`);
                    const data = await resp.json();

                    if (data.changed) {{
                        window.location.href = window.location.pathname;
                    }}

                    setTimeout(poll_moves, 1000);
                }}

                poll_moves();
                </script>
            """)
