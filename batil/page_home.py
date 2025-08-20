from batil.page import Page
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from batil.auth import is_logged_in
from batil.db import get_db, get_table_as_list_of_dicts

from batil.action_form import ActionForm
from batil.action_table import ActionTable

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

            form_existing_games.open_section(1)
            form_existing_games.close_section()
            form_existing_games.close_form()
            self.structured_html.append(form_existing_games.structured_html)



        # New game
        form_new_game = ActionForm("new_game", "New game")
        form_new_game.initialise_tabs(["Rules", "Board", "Opponent"])
        form_new_game.open_section(0)



        form_new_game.close_section()

        form_new_game.open_section(1)
        form_new_game.close_section()

        form_new_game.open_section(2)
        form_new_game.structured_html.append([
            "<p>skibidi</p>",
            "<button type=\"submit\">Post</button>"
            ])
        form_new_game.close_section()
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
