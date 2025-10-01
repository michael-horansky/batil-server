import json
from datetime import datetime, timezone

from batil.html_objects.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.db import get_db, get_table_as_list_of_dicts, conclude_and_rate_game

from batil.engine.game_logic.class_Gamemaster import Gamemaster
from batil.engine.rendering.class_tutorial_HTMLRenderer import TutorialHTMLRenderer
from batil.engine.rendering.class_Abstract_Output import Abstract_Output

from batil.aux_funcs import *


class PageTutorial(Page):

    def __init__(self, tutorial_id, editor_role):
        super().__init__("Tutorial")
        self.tutorial_id = tutorial_id
        self.editor_role = editor_role # "A" or "B", or None if not an editor
        self.client_role = "guest" # default value

        self.gm = Gamemaster(display_logs = False)
        self.refuse_render = False

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
            print(f"ERROR: Attempting to load a non-existing tutorial (tutorial-id = {self.tutorial_id})")
            self.refuse_render = True
            return(None)
        self.game_status = self.tutorial_row["STATUS"]
        self.game_outcome = self.tutorial_row["OUTCOME"]

        # We now identify the user who opened the page
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


    def resolve_tutorial_comments_edit(self):
        db = get_db()
        for key, val in request.form.items():
            print(f"{key} -> {val}")

        if "tcf_action" in request.form:
            if request.form.get("tcf_action") == "edit_tutorial_comment":
                active_turn_index = int(request.form.get("turn_index"))
                db.execute("INSERT OR REPLACE INTO BOC_TUTORIAL_COMMENTS (TUTORIAL_ID, TURN_INDEX, TUTORIAL_COMMENT) VALUES (?, ?, ?)", (self.tutorial_id, active_turn_index, request.form.get("tutorial_comment")))
                db.execute("UPDATE BOC_TUTORIALS SET D_CHANGED = CURRENT_TIMESTAMP WHERE TUTORIAL_ID = ?", (self.tutorial_id,))
                db.commit()

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
        output_message = self.gm.submit_commands(self.editor_role, commands_added)
        if output_message.header == "error":
            db.execute("INSERT INTO BOC_SYSTEM_LOGS (PRIORITY, ORIGIN, MESSAGE) VALUES (4, \"page_tutorial.resolve_command_submission\", ?)", output_message.msg)
            db.commit()
            return(-1)
        new_dynamic_commands = self.gm.dump_changes()
        # We save changes to database
        for turn_index in range(len(new_dynamic_commands)):
            for commander, command_list in new_dynamic_commands[turn_index].items():
                db.execute("INSERT INTO BOC_TUTORIAL_MOVES (TUTORIAL_ID, TURN_INDEX, PLAYER, REPRESENTATION) VALUES (?, ?, ?, ?)", (self.tutorial_id, turn_index, commander, compress_commands(command_rep)))

        if output_message.header == "concluded":
            db.execute("UPDATE BOC_TUTORIALS SET STATUS = \"concluded\", OUTCOME = ? WHERE TUTORIAL_ID = ?", (output_message.msg, self.tutorial_id))
            self.game_status = "concluded"

        db.execute("UPDATE BOC_TUTORIALS SET D_CHANGED = CURRENT_TIMESTAMP WHERE TUTORIAL_ID = ?", (self.tutorial_id,))
        db.commit()

    def load_game(self):
        if self.refuse_render:
            return(None)
        db = get_db()
        # We need to load the static data, the dynamic data, and the ruleset
        static_data_row = db.execute("SELECT T_DIM, X_DIM, Y_DIM, STATIC_REPRESENTATION FROM BOC_BOARDS WHERE BOARD_ID = ?", (self.tutorial_row["BOARD_ID"],)).fetchone()
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
            dynamic_data[row["TURN_INDEX"]][row["PLAYER"]] = decompress_commands(row["REPRESENTATION"])

        ruleset_rows = db.execute("SELECT RULE_GROUP, RULE FROM BOC_TUTORIAL_RULESETS WHERE TUTORIAL_ID = ?", (self.tutorial_id,)).fetchall()
        ruleset = {}
        for row in ruleset_rows:
            ruleset[row["RULE_GROUP"]] = row["RULE"]

        if self.game_status == "in_progress":
            self.gm.load_from_database(static_data, dynamic_data, ruleset)
        else:
            self.gm.load_from_database(static_data, dynamic_data, ruleset, self.game_outcome)

        # We also load the tutorial comments
        tutorial_comment_rows = db.execute("SELECT TURN_INDEX, TUTORIAL_COMMENT FROM BOC_TUTORIAL_COMMENTS WHERE TUTORIAL_ID = ? ORDER BY TURN_INDEX ASC", (self.tutorial_id,)).fetchall()
        self.tutorial_comments = {} #[turn index] = comment; not every index has to exist
        for row in tutorial_comment_rows:
            if row["TUTORIAL_COMMENT"] != "":
                self.tutorial_comments[row["TURN_INDEX"]] = row["TUTORIAL_COMMENT"]




    def prepare_renderer(self):
        # Time for telling the proprietary gamemaster to properly initialise the game with the correct access rights
        # TODO special renderer for tutorials ofc! also client role for editors can be set manually between A and B
        self.gm.prepare_for_rendering(self.editor_role)
        self.renderer = TutorialHTMLRenderer(self.gm.rendering_output, self.tutorial_id, self.tutorial_comments, self.client_role, self.editor_role)
        self.renderer.render_game()


    def render_page(self):
        # First we load the game from database
        #self.load_game()
        # Then we check the POST form to see if new commands were submitted. If yes, we incorporate them into the render object, and also upload them to the db
        #self.resolve_request()
        # Finally, we prepare the rendering object
        if not self.refuse_render:
            self.prepare_renderer()

        self.html_open("boc_tutorial")

        if self.refuse_render:
            self.structured_html.append("ERROR")
        else:
            self.structured_html.append(self.renderer.structured_output)

            self.structured_html.append("</body>")

        return(self.print_html())

