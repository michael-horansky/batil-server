import json

from batil.html_objects.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)

from batil.db import get_db, get_table_as_list_of_dicts

from batil.engine.rendering.class_board_editor_HTMLRenderer import BoardEditorHTMLRenderer


class PageBoardEditor(Page):

    def __init__(self, board_id):
        super().__init__("Board")
        self.board_id = board_id

        self.load_board()

    def resolve_board_edit_submission(self):
        for key, val in request.form.items():
            print(f"  {key} --> {val} ({type(val)})")

        static_stone_data_file = current_app.open_resource("engine/stones/stone_properties.json")
        static_stone_data = json.load(static_stone_data_file)
        static_stone_data_file.close()

        element_keywords_data_file = current_app.open_resource("engine/stones/element_keywords.json")
        element_keywords = json.load(element_keywords_data_file)
        element_keywords_data_file.close()

        try:
            t_dim = int(request.form.get("h_t_dim"))
            x_dim = int(request.form.get("h_x_dim"))
            y_dim = int(request.form.get("h_y_dim"))
            n_bases = int(request.form.get("h_number_of_bases"))
            n_stones = int(request.form.get("h_number_of_stones"))

            static_rep = ""
            for y in range(y_dim):
                for x in range(x_dim):
                    static_rep += request.form.get(f"square_{x}_{y}")

            setup_commands = []
            for i_b in range(n_bases):
                new_command = {"type" : "add_base"}
                for kw_b_i in range(len(element_keywords["bases"])):
                    if element_keywords["bases_types"][kw_b_i] == "int":
                        new_command[element_keywords["bases"][kw_b_i]] = int(request.form.get(f"base_{i_b}_{element_keywords["bases"][kw_b_i]}"))
                    else:
                        new_command[element_keywords["bases"][kw_b_i]] = request.form.get(f"base_{i_b}_{element_keywords["bases"][kw_b_i]}")
                setup_commands.append(new_command)

            for i_s in range(n_stones):
                new_command = {"type" : "add_stone"}
                for kw_s_i in range(len(element_keywords["stones"])):
                    if element_keywords["stones"][kw_s_i] == "a":
                        if not static_stone_data[new_command["stone_type"]]["orientable"]:
                            continue
                    if element_keywords["stones_types"][kw_s_i] == "int":
                        new_command[element_keywords["stones"][kw_s_i]] = int(request.form.get(f"stone_{i_s}_{element_keywords["stones"][kw_s_i]}"))
                    else:
                        new_command[element_keywords["stones"][kw_s_i]] = request.form.get(f"stone_{i_s}_{element_keywords["stones"][kw_s_i]}")
                setup_commands.append(new_command)

            setup_rep = json.dumps(setup_commands)

            board_name = request.form.get("board_name")

        except:
            print("Conversion of inputted board specifications failed!")

        db = get_db()

        db.execute("UPDATE BOC_BOARDS SET T_DIM = ?, X_DIM = ?, Y_DIM = ?, STATIC_REPRESENTATION = ?, SETUP_REPRESENTATION = ?, D_CHANGED = CURRENT_TIMESTAMP, BOARD_NAME = ? WHERE BOARD_ID = ?", (t_dim, x_dim, y_dim, static_rep, setup_rep, board_name, self.board_id))
        db.commit()

    def load_board(self):
        db = get_db()
        #board_row = db.execute("SELECT T_DIM, X_DIM, Y_DIM, STATIC_REPRESENTATION, SETUP_REPRESENTATION, BOARD_NAME, AUTHOR, IS_PUBLIC FROM BOC_BOARDS WHERE BOARD_ID = ?", (self.board_id,)).fetchone()
        board_row = db.execute("""
            SELECT
                BOC_BOARDS.BOARD_ID AS BOARD_ID,
                BOC_BOARDS.T_DIM AS T_DIM,
                BOC_BOARDS.X_DIM AS X_DIM,
                BOC_BOARDS.Y_DIM AS Y_DIM,
                BOC_BOARDS.STATIC_REPRESENTATION AS STATIC_REPRESENTATION,
                BOC_BOARDS.SETUP_REPRESENTATION AS SETUP_REPRESENTATION,
                BOC_BOARDS.BOARD_NAME AS BOARD_NAME,
                BOC_BOARDS.D_PUBLISHED AS D_PUBLISHED,
                BOC_BOARDS.HANDICAP AS HANDICAP,
                BOC_BOARDS.AUTHOR AS AUTHOR,
                BOC_BOARDS.IS_PUBLIC AS IS_PUBLIC,
                COUNT(DISTINCT BOC_GAMES.GAME_ID) AS GAMES_PLAYED,
                COUNT(DISTINCT BOC_USER_SAVED_BOARDS.USERNAME) AS SAVED_BY
            FROM BOC_BOARDS
            LEFT JOIN BOC_GAMES
                ON BOC_GAMES.BOARD_ID = BOC_BOARDS.BOARD_ID
            AND BOC_GAMES.STATUS = "concluded"
            LEFT JOIN BOC_USER_SAVED_BOARDS
                ON BOC_USER_SAVED_BOARDS.BOARD_ID = BOC_BOARDS.BOARD_ID
            WHERE BOC_BOARDS.BOARD_ID = ?
            GROUP BY BOC_BOARDS.BOARD_ID;
            """, (self.board_id,)).fetchone()
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
                    stones.append({"faction" : command["faction"], "stone_type" : command["stone_type"], "x" : command["x"], "y" : command["y"], "a" : command["a"]})
                else:
                    stones.append({"faction" : command["faction"], "stone_type" : command["stone_type"], "x" : command["x"], "y" : command["y"], "a" : None})

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
                "author" : board_row["AUTHOR"],
                "d_published" : board_row["d_published"],
                "handicap" : board_row["HANDICAP"],
                "games_played" : board_row["games_played"],
                "saved_by" : board_row["saved_by"],
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



