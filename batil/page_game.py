import json

from batil.html_objects.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.db import get_db, get_table_as_list_of_dicts

from batil.engine.game_logic.class_Gamemaster import Gamemaster
from batil.engine.rendering.class_HTMLRenderer import HTMLRenderer
from batil.engine.rendering.class_Abstract_Output import Abstract_Output


class PageGame(Page):

    def __init__(self, game_id):
        super().__init__("Game")
        self.game_id = game_id
        self.game_status = None

        self.gm = Gamemaster(display_logs = True)

    def resolve_request(self):
        db = get_db()
        print("Resolving POST...")
        if request.method == 'POST':
            # We check what action is happening
            pass


    def resolve_command_submission(self):
        db = get_db()
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
            db.execute("UPDATE BOC_GAMES SET D_FINISHED = CURRENT_TIMESTAMP, STATUS = \"concluded\", OUTCOME = ? WHERE GAME_ID = ?", (output_message.msg, self.game_id))
            self.game_status = "concluded"

        db.commit()




    def load_game(self):
        db = get_db()
        # We need to load the static data, the dynamic data, and the ruleset

        boc_games_row = db.execute("SELECT BOC_GAMES.PLAYER_A, BOC_GAMES.PLAYER_B, BOC_GAMES.BOARD_ID, BOC_GAMES.STATUS, BOC_GAMES.DRAW_OFFER_STATUS, BOC_GAMES.OUTCOME, BOC_BOARDS.BOARD_NAME AS BOARD_NAME FROM BOC_GAMES INNER JOIN BOC_BOARDS ON BOC_GAMES.BOARD_ID = BOC_BOARDS.BOARD_ID WHERE GAME_ID = ?", (self.game_id,)).fetchone()
        self.game_status = boc_games_row["STATUS"]
        if boc_games_row is None:
            print(f"ERROR: Attempting to load a non-existing game (game-id = {self.game_id})")
            return(-1)

        static_data_row = db.execute("SELECT T_DIM, X_DIM, Y_DIM, STATIC_REPRESENTATION FROM BOC_BOARDS WHERE BOARD_ID = ?", (boc_games_row["BOARD_ID"],)).fetchone()
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

        self.gm.load_from_database(static_data, dynamic_data, ruleset)

        # We now identify the user who opened the page
        self.client_role = None
        self.link_data = {
            "A" : boc_games_row["PLAYER_A"],
            "B" : boc_games_row["PLAYER_B"],
            "board" : boc_games_row["BOARD_ID"],
            "board_name" : boc_games_row["BOARD_NAME"]
            }
        #self.users_to_link = []
        if g.user is not None:
            if boc_games_row["STATUS"] == "in_progress":
                if g.user["username"] == boc_games_row["PLAYER_A"]:
                    self.client_role = "A"
                elif g.user["username"] == boc_games_row["PLAYER_B"]:
                    self.client_role = "B"
                else:
                    self.client_role = "guest"
            else:
                self.client_role = "guest"




    def prepare_renderer(self):
        # Time for telling the proprietary gamemaster to properly initialise the game with the correct access rights
        self.gm.prepare_for_rendering(self.client_role)
        self.renderer = HTMLRenderer(self.gm.rendering_output, self.game_id, self.client_role)
        self.renderer.render_game(self.link_data)


    def render_page(self):
        # First we load the game from database
        #self.load_game()
        # Then we check the POST form to see if new commands were submitted. If yes, we incorporate them into the render object, and also upload them to the db
        #self.resolve_request()
        # Finally, we prepare the rendering object
        self.prepare_renderer()

        self.html_open("boc_ingame")

        self.structured_html.append(self.renderer.structured_output)

        if self.gm.rendering_output.did_player_finish_turn and self.game_status == "in_progress":
            # The client is waiting for his opponent; we will check the page automatically once the game has been updated
            self.clientside_reloader()

        self.structured_html.append("</body>")

        return(self.print_html())


    def clientside_reloader(self):
        # Prepares a JS daemon which checks whether to reload the game
        db = get_db()
        initial_move_count = current_count = db.execute(
            "SELECT COUNT(*) AS cnt FROM BOC_MOVES WHERE GAME_ID = ?", (self.game_id,)
        ).fetchone()["cnt"]
        self.structured_html.append(f"""
            <script>
            let move_count = {initial_move_count};
            let move_count_url = \"{url_for("game_bp.moves_count", game_id=self.game_id)}\";

            async function poll_moves() {{
                const resp = await fetch(`${{move_count_url}}?count=${{move_count}}`);
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
