import json

from batil.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.auth import is_logged_in
from batil.db import get_db, get_table_as_list_of_dicts

from batil.engine.game_logic.class_Gamemaster import Gamemaster
from batil.engine.rendering.class_HTMLRenderer import HTMLRenderer


class PageGame(Page):

    def __init__(self, game_id):
        super().__init__()
        self.game_id = game_id

        print("----------------")
        print(self.game_id)
        print(type(self.game_id))

        self.gm = Gamemaster(display_logs = True)

    def resolve_request(self):
        print("Resolving POST...")

    def load_game(self):
        db = get_db()
        # We need to load the static data, the dynamic data, and the ruleset

        boc_games_row = db.execute("SELECT PLAYER_A, PLAYER_B, BOARD_ID, STATUS, DRAW_OFFER_STATUS, OUTCOME FROM BOC_GAMES WHERE GAME_ID = ?", (self.game_id,)).fetchone()
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
        self.client_role = "guest"
        if g.user["username"] is not None:
            if boc_games_row["STATUS"] == "in_progress":
                if g.user["username"] == boc_games_row["PLAYER_A"]:
                    self.client_role = "A"
                elif g.user["username"] == boc_games_row["PLAYER_B"]:
                    self.client_role = "B"

        # Time for telling the proprietary gamemaster to properly initialise the game with the correct access rights
        self.gm.open_game(self.client_role)

    def prepare_renderer(self):
        self.renderer = HTMLRenderer(self.gm.rendering_output)
        self.renderer.render_game()


    def render_page(self):
        self.resolve_request()

        self.load_game()
        self.prepare_renderer()

        self.html_open("Game", "boc_ingame")

        self.structured_html.append(self.renderer.structured_output)

        return(self.print_html())
