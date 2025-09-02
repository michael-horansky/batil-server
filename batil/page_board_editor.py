import json

from batil.html_objects.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.db import get_db, get_table_as_list_of_dicts

from batil.engine.rendering.class_board_editor_HTMLRenderer import BoardEditorHTMLRenderer


class PageBoardEditor(Page):

    def __init__(self, board_id):
        super().__init__("Board")
        self.board_id = board_id

        self.load_board()

    def resolve_board_edit_submission(self):
        print(f"Board {self.board_id} was updated!")

    def load_board(self):
        db = get_db()
        board_row = db.execute("SELECT T_DIM, X_DIM, Y_DIM, STATIC_REPRESENTATION, SETUP_REPRESENTATION, BOARD_NAME, AUTHOR, IS_PUBLIC FROM BOC_BOARDS WHERE BOARD_ID = ?", (self.board_id,)).fetchone()
        static_representation = board_row["STATIC_REPRESENTATION"]
        setup_representation = board_row["SETUP_REPRESENTATION"]

        board_static = []
        for i in range(board_row["X_DIM"]):
            board_static.append([' ']*board_row["Y_DIM"])
        for y in range(board_row["Y_DIM"]):
            for x in range(board_row["X_DIM"]):
                cur_char = static_representation[y * board_row["X_DIM"] + x]
                board_static[x][y] = cur_char

        setup_commands = json.loads(setup_representation)

        # To simplify things, we do not deal directly with commands, but simply with a list of stones and a list of bases
        bases = [] # [base index] = {"faction" : "A/B/neutral", "x", "y"}
        stones = [] # [stone index] = {"faction" : "A/B/GM", "type" : "tank/...", "x", "y", "a"}

        for command in setup_commands:
            if command["type"] == "add_base":
                bases.append({"faction" : command["faction"], "x" : command["x"], "y" : command["y"]})
            elif command["type"] == "add_stone":
                if "a" in command.keys():
                    stones.append({"faction" : command["faction"], "type" : command["stone_type"], "x" : command["x"], "y" : command["y"], "a" : command["a"]})
                else:
                    stones.append({"faction" : command["faction"], "type" : command["stone_type"], "x" : command["x"], "y" : command["y"]})

        if board_row["IS_PUBLIC"] == 0 and board_row["AUTHOR"] == g.user["username"]:
            client_action = "edit"
        else:
            client_action = "view"

        self.render_object = {
                "t_dim" : board_row["T_DIM"],
                "x_dim" : board_row["X_DIM"],
                "y_dim" : board_row["Y_DIM"],
                "board_static" : board_static,
                "stones" : stones,
                "bases" : bases,
                "board_name" : board_row["BOARD_NAME"],
                "client_action" : client_action
            }

    def prepare_renderer(self):
        self.renderer = BoardEditorHTMLRenderer(self.render_object, self.board_id)
        self.renderer.render_board()

    def render_page(self):
        self.prepare_renderer()

        self.html_open("boc_board_editor")

        self.structured_html.append(self.renderer.structured_output)

        self.structured_html.append("</body>")

        return(self.print_html())



